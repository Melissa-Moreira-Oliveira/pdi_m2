import cv2
import sys
import os
import json
import argparse
import numpy as np

def build_parser():
    parser = argparse.ArgumentParser(prog="pdi_lab")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    parser.add_argument("--operation", required=True, choices=[
        "segment",
        "analyze",
    ])
    parser.add_argument("--method", choices=[
        "fixed",
        "otsu",
        "adaptive",
        "hsv",
    ])
    parser.add_argument("--threshold", type=int)
    parser.add_argument("--blur", type=int, default=0)
    parser.add_argument("--invert", action="store_true")
    parser.add_argument("--block-size", type=int, default=51)
    parser.add_argument("--constant", type=int, default=5)
    parser.add_argument("--hmin", type=int, default=0)
    parser.add_argument("--hmax", type=int, default=179)
    parser.add_argument("--smin", type=int, default=0)
    parser.add_argument("--smax", type=int, default=255)
    parser.add_argument("--vmin", type=int, default=0)
    parser.add_argument("--vmax", type=int, default=255)
    parser.add_argument("--overlay")
    parser.add_argument("--connectivity", type=int, default=8, choices=[4, 8])
    parser.add_argument("--min-area", type=int, default=0)
    parser.add_argument("--sequence", default="open,close")
    parser.add_argument("--kernel-sizes", default="7,15")
    parser.add_argument("--iterations", default="1,1")
    parser.add_argument("--kernel-shape", default="ellipse", choices=["ellipse", "rect", "cross"])

    return parser

def main():
    args = build_parser().parse_args()
    operations = {
        "segment": op_segment,
        "analyze": op_analyze,
    }
    func = operations.get(args.operation)
    if func is None:
        print(f"operação inválida: {args.operation}", file=sys.stderr)
        return 1
    if args.output is None:
        print(f"--output é obrigatório para a operação {args.operation}", file=sys.stderr)
        return 1
    return func(args)

def op_segment(args):
    # máscara binária: 0 = fundo, 255 = objeto
    img = cv2.imread(args.input)
    if img is None:
        print(f"não foi possível abrir a imagem {args.input}", file=sys.stderr)
        return 1
    if args.method is None:
        print(f"--method é obrigatório para a operação {args.operation}", file=sys.stderr)
        return 1
    if args.blur < 0 or (args.blur > 0 and args.blur % 2 == 0):
        print(f"--blur deve ser 0 ou um número ímpar positivo: {args.blur}", file=sys.stderr)
        return 1

    # pré-processamento (o mesmo para as duas configurações comparadas)
    if args.blur > 0:
        suavizada = cv2.GaussianBlur(img, (args.blur, args.blur), 0)
    else:
        suavizada = img

    if args.method == "fixed":
        mascara = metodo_fixed(suavizada, args)
    elif args.method == "otsu":
        mascara = metodo_otsu(suavizada, args)
    elif args.method == "adaptive":
        mascara = metodo_adaptive(suavizada, args)
    else:
        mascara = metodo_hsv(suavizada, args)

    if mascara is None:
        return 1

    # objeto escuro: a inversão é aplicada depois da limiarização
    if args.invert:
        mascara = cv2.bitwise_not(mascara)

    totalPixels = mascara.shape[0] * mascara.shape[1]
    pixelsObjeto = int(np.count_nonzero(mascara))
    proporcao = 100 * pixelsObjeto / totalPixels

    print(f"Método: {args.method}")
    print(f"Pré-processamento: {descreve_blur(args)}")
    print(f"Parâmetros: {descreve_parametros(args)}")
    if args.invert:
        print("Inversão aplicada: sim (o objeto é mais escuro que o fundo)")
    else:
        print("Inversão aplicada: não")
    print(f"Pixels de primeiro plano: {pixelsObjeto} de {totalPixels} ({proporcao:.2f}%)")

    if confere_mascara(mascara, img) == False:
        return 1

    if salva_imagem(args.output, mascara) == False:
        return 1

    print(f"Máscara salva em: {args.output}")

    if args.overlay is not None:
        sobreposicao = monta_sobreposicao(img, mascara)
        if salva_imagem(args.overlay, sobreposicao) == False:
            return 1
        print(f"Sobreposição salva em: {args.overlay}")

    return 0

def op_analyze(args):
    # aqui a entrada é a máscara do segment e a saída é um prefixo de arquivos
    mascara = cv2.imread(args.input, cv2.IMREAD_GRAYSCALE)
    if mascara is None:
        print(f"não foi possível abrir a máscara {args.input}", file=sys.stderr)
        return 1
    if args.min_area < 0:
        print(f"--min-area não pode ser negativo: {args.min_area}", file=sys.stderr)
        return 1
    if confere_binaria(mascara) == False:
        return 1

    prefixo = args.output
    print(f"Máscara inicial: {mascara.shape[1]}x{mascara.shape[0]}, 1 canal")
    print(f"Conectividade usada na análise: {args.connectivity}")
    print(f"Filtro por área: --min-area {args.min_area}")

    # 1) a cópia da máscara inicial é guardada antes de qualquer operação
    if salva_imagem(prefixo + "_mask_initial.png", mascara) == False:
        return 1

    # 2) contagem nas duas conectividades, na mesma máscara
    componentes4 = rotula(mascara, 4)
    componentes8 = rotula(mascara, 8)
    print(f"Componentes na máscara inicial com conectividade 4: {componentes4[0]}")
    print(f"Componentes na máscara inicial com conectividade 8: {componentes8[0]}")

    inicial = rotula(mascara, args.connectivity)
    escreve_csv(prefixo + "_initial.csv", inicial, args.min_area)
    mantidosInicial = conta_mantidos(inicial, args.min_area)
    areaInicial = int(np.count_nonzero(mascara))

    # 3) sequência morfológica
    final, estagios = aplica_sequencia(mascara, args, prefixo)
    if final is None:
        return 1

    if salva_imagem(prefixo + "_mask_final.png", final) == False:
        return 1

    # 4) recontagem na máscara final
    depois = rotula(final, args.connectivity)
    escreve_csv(prefixo + "_final.csv", depois, args.min_area)
    mantidosFinal = conta_mantidos(depois, args.min_area)
    areaFinal = int(np.count_nonzero(final))

    imagemRotulos = desenha_rotulos(depois, args.min_area)
    if salva_imagem(prefixo + "_labels.png", imagemRotulos) == False:
        return 1

    resumo = {
        "input": args.input,
        "connectivity": args.connectivity,
        "min_area": args.min_area,
        "components_initial_c4": componentes4[0],
        "components_initial_c8": componentes8[0],
        "morphology": {
            "sequence": [estagio["operation"] for estagio in estagios],
            "kernel_shape": args.kernel_shape,
            "kernel_sizes": [estagio["kernel_size"] for estagio in estagios],
            "iterations": [estagio["iterations"] for estagio in estagios],
            "stages": estagios,
        },
        "initial": {
            "components_raw": inicial[0],
            "components_kept": mantidosInicial,
            "foreground_pixels": areaInicial,
        },
        "final": {
            "components_raw": depois[0],
            "components_kept": mantidosFinal,
            "foreground_pixels": areaFinal,
        },
    }
    if escreve_json(prefixo + "_summary.json", resumo) == False:
        return 1

    print("")
    print("tabela antes/depois")
    print("etapa    componentes_brutos  componentes_filtrados  area_total")
    print(f"inicial  {inicial[0]:<18} {mantidosInicial:<22} {areaInicial}")
    print(f"final    {depois[0]:<18} {mantidosFinal:<22} {areaFinal}")
    print("")
    print(f"Arquivos gerados com o prefixo: {prefixo}")

    return 0

def metodo_fixed(img, args):
    # g(x,y) = 255 se f(x,y) > T, senão 0 (convenção do cv2.threshold)
    if args.threshold is None:
        print(f"--threshold é obrigatório para o método {args.method}", file=sys.stderr)
        return None
    if args.threshold < 0 or args.threshold > 255:
        print(f"--threshold deve estar entre 0 e 255: {args.threshold}", file=sys.stderr)
        return None

    cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    limiar, mascara = cv2.threshold(cinza, args.threshold, 255, cv2.THRESH_BINARY)
    return mascara

def metodo_otsu(img, args):
    # o próprio Otsu escolhe o limiar olhando o histograma
    cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    limiar, mascara = cv2.threshold(cinza, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    print(f"Limiar escolhido pelo Otsu: {int(limiar)}")
    return mascara

def metodo_adaptive(img, args):
    # limiar calculado por vizinhança de tamanho --block-size
    if args.block_size < 3 or args.block_size % 2 == 0:
        print(f"--block-size deve ser ímpar e maior ou igual a 3: {args.block_size}", file=sys.stderr)
        return None

    cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mascara = cv2.adaptiveThreshold(cinza, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY, args.block_size, args.constant)
    return mascara

def metodo_hsv(img, args):
    # seleção de intervalo em HSV, com H de 0 a 179 na escala do OpenCV
    if confere_intervalo_hsv(args) == False:
        return None

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    if args.hmin <= args.hmax:
        inferior = np.array([args.hmin, args.smin, args.vmin])
        superior = np.array([args.hmax, args.smax, args.vmax])
        mascara = cv2.inRange(hsv, inferior, superior)
    else:
        # o intervalo cruza a descontinuidade do matiz (ex.: vermelho), então viram dois pedaços
        primeiro = cv2.inRange(hsv, np.array([args.hmin, args.smin, args.vmin]),
                               np.array([179, args.smax, args.vmax]))
        segundo = cv2.inRange(hsv, np.array([0, args.smin, args.vmin]),
                              np.array([args.hmax, args.smax, args.vmax]))
        mascara = cv2.bitwise_or(primeiro, segundo)
        print("Intervalo de matiz cruzando o 0, a máscara foi montada com duas faixas.")

    return mascara

def aplica_sequencia(mascara, args, prefixo):
    # a sequência vem pela linha de comando, sem precisar mexer no código
    operacoes = separa_lista(args.sequence)
    tamanhos = separa_lista(args.kernel_sizes)
    repeticoes = separa_lista(args.iterations)

    if len(operacoes) < 2:
        print("--sequence precisa de pelo menos duas operações, ex.: open,close", file=sys.stderr)
        return None, None
    if len(tamanhos) != len(operacoes) or len(repeticoes) != len(operacoes):
        print("--kernel-sizes e --iterations precisam ter um valor para cada operação de --sequence",
              file=sys.stderr)
        return None, None

    temAberturaOuFechamento = False
    for operacao in operacoes:
        if operacao == "open" or operacao == "close":
            temAberturaOuFechamento = True
    if temAberturaOuFechamento == False:
        print("--sequence precisa ter pelo menos uma abertura (open) ou um fechamento (close)",
              file=sys.stderr)
        return None, None

    formas = {
        "ellipse": cv2.MORPH_ELLIPSE,
        "rect": cv2.MORPH_RECT,
        "cross": cv2.MORPH_CROSS,
    }
    tiposMorfologia = {
        "open": cv2.MORPH_OPEN,
        "close": cv2.MORPH_CLOSE,
        "erode": cv2.MORPH_ERODE,
        "dilate": cv2.MORPH_DILATE,
    }

    atual = mascara
    estagios = []
    for i in range(len(operacoes)):
        operacao = operacoes[i]
        if tiposMorfologia.get(operacao) is None:
            print(f"operação morfológica desconhecida: {operacao}", file=sys.stderr)
            return None, None

        tamanho = converte_inteiro(tamanhos[i])
        if tamanho is None or tamanho < 1 or tamanho % 2 == 0:
            print(f"--kernel-sizes deve ter números ímpares positivos: {tamanhos[i]}", file=sys.stderr)
            return None, None

        quantidade = converte_inteiro(repeticoes[i])
        if quantidade is None or quantidade < 1:
            print(f"--iterations deve ter números inteiros maiores que 0: {repeticoes[i]}", file=sys.stderr)
            return None, None

        elemento = cv2.getStructuringElement(formas[args.kernel_shape], (tamanho, tamanho))
        anterior = int(np.count_nonzero(atual))
        atual = cv2.morphologyEx(atual, tiposMorfologia[operacao], elemento, iterations=quantidade)
        depois = int(np.count_nonzero(atual))

        arquivo = f"{prefixo}_stage{i + 1}_{operacao}.png"
        if salva_imagem(arquivo, atual) == False:
            return None, None

        print(f"Estágio {i + 1}: {operacao}, elemento {args.kernel_shape} {tamanho}x{tamanho}, "
              f"{quantidade} iteração(ões), primeiro plano {anterior} -> {depois}")

        estagios.append({
            "stage": i + 1,
            "operation": operacao,
            "kernel_shape": args.kernel_shape,
            "kernel_size": tamanho,
            "iterations": quantidade,
            "foreground_before": anterior,
            "foreground_after": depois,
            "file": arquivo,
        })

    return atual, estagios

def rotula(mascara, conectividade):
    quantidade, rotulos, estatisticas, centroides = cv2.connectedComponentsWithStats(
        mascara, connectivity=conectividade)
    # o rótulo 0 é o fundo, por isso ele não entra na contagem
    return quantidade - 1, rotulos, estatisticas, centroides

def conta_mantidos(resultado, minArea):
    quantidade, rotulos, estatisticas, centroides = resultado
    mantidos = 0
    for rotulo in range(1, quantidade + 1):
        if estatisticas[rotulo, cv2.CC_STAT_AREA] >= minArea:
            mantidos += 1
    return mantidos

def escreve_csv(caminho, resultado, minArea):
    quantidade, rotulos, estatisticas, centroides = resultado
    if garante_pasta(caminho) == False:
        return False

    arquivo = open(caminho, "w")
    arquivo.write("label,area,x,y,width,height,cx,cy,kept\n")
    for rotulo in range(1, quantidade + 1):
        area = estatisticas[rotulo, cv2.CC_STAT_AREA]
        x = estatisticas[rotulo, cv2.CC_STAT_LEFT]
        y = estatisticas[rotulo, cv2.CC_STAT_TOP]
        largura = estatisticas[rotulo, cv2.CC_STAT_WIDTH]
        altura = estatisticas[rotulo, cv2.CC_STAT_HEIGHT]
        cx = centroides[rotulo][0]
        cy = centroides[rotulo][1]

        if area >= minArea:
            mantido = "true"
        else:
            mantido = "false"

        arquivo.write(f"{rotulo},{area},{x},{y},{largura},{altura},{cx:.1f},{cy:.1f},{mantido}\n")
    arquivo.close()
    return True

def desenha_rotulos(resultado, minArea):
    # cada componente ganha uma cor pelo número do rótulo, então a imagem sai sempre igual
    quantidade, rotulos, estatisticas, centroides = resultado
    altura = rotulos.shape[0]
    largura = rotulos.shape[1]

    colorida = np.zeros((altura, largura, 3), dtype=np.uint8)
    for rotulo in range(1, quantidade + 1):
        matiz = (rotulo * 35) % 180
        cor = cv2.cvtColor(np.uint8([[[matiz, 255, 255]]]), cv2.COLOR_HSV2BGR)
        colorida[rotulos == rotulo] = cor[0][0]

    for rotulo in range(1, quantidade + 1):
        area = estatisticas[rotulo, cv2.CC_STAT_AREA]
        if area < minArea:
            continue
        x = estatisticas[rotulo, cv2.CC_STAT_LEFT]
        y = estatisticas[rotulo, cv2.CC_STAT_TOP]
        largura = estatisticas[rotulo, cv2.CC_STAT_WIDTH]
        altura = estatisticas[rotulo, cv2.CC_STAT_HEIGHT]
        cv2.rectangle(colorida, (x, y), (x + largura, y + altura), (255, 255, 255), 2)
        cv2.putText(colorida, str(rotulo), (x, max(y - 5, 12)), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (255, 255, 255), 2)

    return colorida

def escreve_json(caminho, resumo):
    if garante_pasta(caminho) == False:
        return False

    arquivo = open(caminho, "w")
    arquivo.write(json.dumps(resumo, indent=2))
    arquivo.close()
    return True

def confere_intervalo_hsv(args):
    if args.hmin < 0 or args.hmin > 179 or args.hmax < 0 or args.hmax > 179:
        print(f"--hmin e --hmax devem estar entre 0 e 179: {args.hmin} e {args.hmax}", file=sys.stderr)
        return False
    if args.smin < 0 or args.smin > 255 or args.smax < 0 or args.smax > 255:
        print(f"--smin e --smax devem estar entre 0 e 255: {args.smin} e {args.smax}", file=sys.stderr)
        return False
    if args.vmin < 0 or args.vmin > 255 or args.vmax < 0 or args.vmax > 255:
        print(f"--vmin e --vmax devem estar entre 0 e 255: {args.vmin} e {args.vmax}", file=sys.stderr)
        return False
    if args.smin > args.smax or args.vmin > args.vmax:
        print("--smin não pode ser maior que --smax e --vmin não pode ser maior que --vmax", file=sys.stderr)
        return False
    return True

def confere_mascara(mascara, img):
    # confere o que o enunciado pede: mesmo tamanho, um canal e só 0 e 255
    if mascara.shape[0] != img.shape[0] or mascara.shape[1] != img.shape[1]:
        print("a máscara não tem a mesma largura e altura da entrada", file=sys.stderr)
        return False
    if confere_binaria(mascara) == False:
        return False

    print(f"Máscara verificada: {mascara.shape[1]}x{mascara.shape[0]}, 1 canal")
    return True

def confere_binaria(mascara):
    if len(mascara.shape) != 2:
        print(f"a máscara deveria ter um canal só: {mascara.shape}", file=sys.stderr)
        return False

    valores = []
    for valor in np.unique(mascara):
        if valor != 0 and valor != 255:
            print(f"a máscara tem um valor que não é 0 nem 255: {valor}", file=sys.stderr)
            return False
        valores.append(int(valor))

    print(f"Valores encontrados na máscara: {valores}")
    return True

def monta_sobreposicao(img, mascara):
    # pinta de vermelho o que a máscara marcou como objeto, para dar pra ver os erros
    colorida = np.zeros_like(img)
    colorida[mascara > 0] = (0, 0, 255)
    sobreposicao = cv2.addWeighted(img, 0.7, colorida, 0.3, 0)

    contornos, hierarquia = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(sobreposicao, contornos, -1, (0, 255, 255), 2)
    return sobreposicao

def salva_imagem(caminho, img):
    if garante_pasta(caminho) == False:
        return False

    if cv2.imwrite(caminho, img) == False:
        print(f"não foi possível salvar o arquivo {caminho}", file=sys.stderr)
        return False
    return True

def garante_pasta(caminho):
    pasta = os.path.dirname(caminho)
    if pasta != "" and os.path.isdir(pasta) == False:
        os.makedirs(pasta)
    return True

def separa_lista(texto):
    pedacos = []
    for pedaco in texto.split(","):
        pedacos.append(pedaco.strip())
    return pedacos

def converte_inteiro(texto):
    if texto.isdigit() == False:
        return None
    return int(texto)

def descreve_blur(args):
    if args.blur > 0:
        return f"GaussianBlur {args.blur}x{args.blur}"
    else:
        return "nenhum"

def descreve_parametros(args):
    if args.method == "fixed":
        return f"--threshold {args.threshold}"
    elif args.method == "otsu":
        return "limiar automático"
    elif args.method == "adaptive":
        return f"--block-size {args.block_size} --constant {args.constant}"
    else:
        return (f"--hmin {args.hmin} --hmax {args.hmax} --smin {args.smin} "
                f"--smax {args.smax} --vmin {args.vmin} --vmax {args.vmax}")

if __name__ == "__main__":
    sys.exit(main())
