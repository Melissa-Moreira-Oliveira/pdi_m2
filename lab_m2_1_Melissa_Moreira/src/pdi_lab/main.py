import cv2
import sys
import os
import argparse
import numpy as np

def build_parser():
    parser = argparse.ArgumentParser(prog="pdi_lab")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    parser.add_argument("--operation", required=True, choices=[
        "segment",
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

    return parser

def main():
    args = build_parser().parse_args()
    operations = {
        "segment": op_segment,
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
    if len(mascara.shape) != 2:
        print(f"a máscara deveria ter um canal só: {mascara.shape}", file=sys.stderr)
        return False
    if mascara.shape[0] != img.shape[0] or mascara.shape[1] != img.shape[1]:
        print("a máscara não tem a mesma largura e altura da entrada", file=sys.stderr)
        return False

    valores = []
    for valor in np.unique(mascara):
        if valor != 0 and valor != 255:
            print(f"a máscara tem um valor que não é 0 nem 255: {valor}", file=sys.stderr)
            return False
        valores.append(int(valor))

    print(f"Máscara verificada: {mascara.shape[1]}x{mascara.shape[0]}, 1 canal, valores {valores}")
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
    pasta = os.path.dirname(caminho)
    if pasta != "" and os.path.isdir(pasta) == False:
        os.makedirs(pasta)

    if cv2.imwrite(caminho, img) == False:
        print(f"não foi possível salvar o arquivo {caminho}", file=sys.stderr)
        return False
    return True

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
