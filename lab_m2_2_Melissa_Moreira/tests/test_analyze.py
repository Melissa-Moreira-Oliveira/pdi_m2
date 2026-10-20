import os
import sys
import json
import subprocess
import cv2
import numpy as np

PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROGRAMA = os.path.join("src", "pdi_lab", "main.py")
PASTA_SAIDA = os.path.join("tests", "saida")

def roda(*argumentos):
    comando = [sys.executable, PROGRAMA] + list(argumentos)
    return subprocess.run(comando, cwd=PROJETO, capture_output=True, text=True)

def caminho(nome):
    pasta = os.path.join(PROJETO, PASTA_SAIDA)
    if os.path.isdir(pasta) == False:
        os.makedirs(pasta)
    return os.path.join(PASTA_SAIDA, nome)

def salva_mascara(nome, matriz):
    cv2.imwrite(os.path.join(PROJETO, nome), matriz)
    return nome

def le_imagem(nome):
    return cv2.imread(os.path.join(PROJETO, nome), cv2.IMREAD_GRAYSCALE)

def le_resumo(prefixo):
    arquivo = open(os.path.join(PROJETO, prefixo + "_summary.json"))
    resumo = json.load(arquivo)
    arquivo.close()
    return resumo

def le_csv(nome):
    arquivo = open(os.path.join(PROJETO, nome))
    linhas = arquivo.read().strip().split("\n")
    arquivo.close()

    componentes = []
    for linha in linhas[1:]:
        if linha == "":
            continue
        partes = linha.split(",")
        componentes.append({
            "label": int(partes[0]),
            "area": int(partes[1]),
            "x": int(partes[2]),
            "y": int(partes[3]),
            "width": int(partes[4]),
            "height": int(partes[5]),
            "kept": partes[8],
        })
    return linhas[0], componentes

def test_dois_pixels_na_diagonal():
    # conectividade 4 enxerga 2 componentes, conectividade 8 enxerga 1
    matriz = np.zeros((5, 5), dtype=np.uint8)
    matriz[1, 1] = 255
    matriz[2, 2] = 255
    entrada = salva_mascara(caminho("diagonal.png"), matriz)

    resultado = roda("--input", entrada, "--output", caminho("diagonal"), "--operation", "analyze",
                     "--sequence", "open,close", "--kernel-sizes", "3,3")
    assert resultado.returncode == 0

    resumo = le_resumo(caminho("diagonal"))
    assert resumo["components_initial_c4"] == 2
    assert resumo["components_initial_c8"] == 1

def test_abertura_tira_o_ruido():
    # quadrado grande + pontinhos soltos: a abertura com elemento 5x5 derruba os pontinhos
    matriz = np.zeros((60, 60), dtype=np.uint8)
    matriz[10:40, 10:40] = 255
    matriz[50, 5] = 255
    matriz[52, 55] = 255
    matriz[5, 50:52] = 255
    entrada = salva_mascara(caminho("ruido.png"), matriz)

    resultado = roda("--input", entrada, "--output", caminho("ruido"), "--operation", "analyze",
                     "--sequence", "open,close", "--kernel-sizes", "5,5", "--connectivity", "8")
    assert resultado.returncode == 0

    resumo = le_resumo(caminho("ruido"))
    assert resumo["initial"]["components_raw"] == 4
    assert resumo["final"]["components_raw"] == 1

    depoisAbertura = le_imagem(caminho("ruido_stage1_open.png"))
    assert depoisAbertura[50, 5] == 0
    assert depoisAbertura[52, 55] == 0
    assert depoisAbertura[25, 25] == 255

def test_fechamento_fecha_o_furo():
    # quadrado com um furo pequeno no meio: o fechamento com elemento 9x9 fecha o furo
    matriz = np.zeros((60, 60), dtype=np.uint8)
    matriz[10:50, 10:50] = 255
    matriz[28:32, 28:32] = 0
    entrada = salva_mascara(caminho("furo.png"), matriz)

    resultado = roda("--input", entrada, "--output", caminho("furo"), "--operation", "analyze",
                     "--sequence", "open,close", "--kernel-sizes", "3,9")
    assert resultado.returncode == 0

    antes = le_imagem(caminho("furo_mask_initial.png"))
    depois = le_imagem(caminho("furo_mask_final.png"))
    assert antes[30, 30] == 0
    assert depois[30, 30] == 255

def test_mascara_vazia():
    matriz = np.zeros((30, 30), dtype=np.uint8)
    entrada = salva_mascara(caminho("vazia.png"), matriz)

    resultado = roda("--input", entrada, "--output", caminho("vazia"), "--operation", "analyze")
    assert resultado.returncode == 0

    resumo = le_resumo(caminho("vazia"))
    assert resumo["initial"]["components_raw"] == 0
    assert resumo["final"]["components_raw"] == 0
    assert resumo["final"]["foreground_pixels"] == 0

    cabecalho, componentes = le_csv(caminho("vazia_final.csv"))
    assert cabecalho == "label,area,x,y,width,height,cx,cy,kept"
    assert len(componentes) == 0

def test_objeto_tocando_a_borda():
    matriz = np.zeros((40, 40), dtype=np.uint8)
    matriz[0:20, 0:20] = 255
    entrada = salva_mascara(caminho("borda.png"), matriz)

    resultado = roda("--input", entrada, "--output", caminho("borda"), "--operation", "analyze",
                     "--sequence", "open,close", "--kernel-sizes", "3,3")
    assert resultado.returncode == 0

    cabecalho, componentes = le_csv(caminho("borda_initial.csv"))
    assert len(componentes) == 1
    assert componentes[0]["x"] == 0
    assert componentes[0]["y"] == 0
    assert componentes[0]["area"] == 400

def test_parametros_invalidos():
    matriz = np.zeros((20, 20), dtype=np.uint8)
    matriz[5:15, 5:15] = 255
    entrada = salva_mascara(caminho("quadrado.png"), matriz)
    saida = caminho("quadrado")

    # conectividade que não existe
    resultado = roda("--input", entrada, "--output", saida, "--operation", "analyze",
                     "--connectivity", "6")
    assert resultado.returncode != 0

    # área mínima negativa
    resultado = roda("--input", entrada, "--output", saida, "--operation", "analyze",
                     "--min-area", "-5")
    assert resultado.returncode != 0

    # sequência com uma operação só
    resultado = roda("--input", entrada, "--output", saida, "--operation", "analyze",
                     "--sequence", "open", "--kernel-sizes", "3", "--iterations", "1")
    assert resultado.returncode != 0

    # operação morfológica que não existe
    resultado = roda("--input", entrada, "--output", saida, "--operation", "analyze",
                     "--sequence", "open,enfeitar", "--kernel-sizes", "3,3")
    assert resultado.returncode != 0

    # elemento estruturante de tamanho par
    resultado = roda("--input", entrada, "--output", saida, "--operation", "analyze",
                     "--sequence", "open,close", "--kernel-sizes", "4,3")
    assert resultado.returncode != 0

    # quantidade de tamanhos diferente da quantidade de operações
    resultado = roda("--input", entrada, "--output", saida, "--operation", "analyze",
                     "--sequence", "open,close", "--kernel-sizes", "3")
    assert resultado.returncode != 0

def test_entrada_que_nao_e_binaria():
    matriz = np.zeros((20, 20), dtype=np.uint8)
    matriz[5:15, 5:15] = 128
    entrada = salva_mascara(caminho("cinza.png"), matriz)

    resultado = roda("--input", entrada, "--output", caminho("cinza"), "--operation", "analyze")
    assert resultado.returncode != 0

def test_falha_de_leitura():
    resultado = roda("--input", caminho("nao_existe.png"), "--output", caminho("nada"),
                     "--operation", "analyze")
    assert resultado.returncode != 0

def test_imagens_do_estudo():
    # as duas imagens, do segment até o analyze, conferindo a soma das áreas
    casos = [
        ("images/input/catdonut.jpg", "donut",
         ["--method", "hsv", "--smin", "120", "--blur", "5"]),
        ("images/input/gato_uva.png", "uva",
         ["--method", "hsv", "--hmin", "30", "--hmax", "85", "--smin", "80", "--blur", "5"]),
        ("images/input/gato_chinchilla.png", "chinchilla",
         ["--method", "hsv", "--smax", "40", "--blur", "5"]),
    ]
    for entrada, nome, parametros in casos:
        mascara = caminho(nome + "_mask.png")
        resultado = roda("--input", entrada, "--output", mascara, "--operation", "segment", *parametros)
        assert resultado.returncode == 0

        prefixo = caminho(nome)
        resultado = roda("--input", mascara, "--output", prefixo, "--operation", "analyze",
                         "--connectivity", "8", "--min-area", "500",
                         "--sequence", "open,close", "--kernel-sizes", "7,15", "--iterations", "1,1")
        assert resultado.returncode == 0

        # os estágios intermediários e os csv precisam existir
        assert os.path.isfile(os.path.join(PROJETO, prefixo + "_stage1_open.png"))
        assert os.path.isfile(os.path.join(PROJETO, prefixo + "_stage2_close.png"))
        assert os.path.isfile(os.path.join(PROJETO, prefixo + "_labels.png"))

        # a soma das áreas brutas tem que bater com os pixels de primeiro plano da máscara
        for etapa, arquivo in [("initial", prefixo + "_mask_initial.png"),
                               ("final", prefixo + "_mask_final.png")]:
            cabecalho, componentes = le_csv(prefixo + "_" + etapa + ".csv")
            soma = 0
            for componente in componentes:
                soma += componente["area"]
            assert soma == np.count_nonzero(le_imagem(arquivo))

if __name__ == "__main__":
    testes = [
        test_dois_pixels_na_diagonal,
        test_abertura_tira_o_ruido,
        test_fechamento_fecha_o_furo,
        test_mascara_vazia,
        test_objeto_tocando_a_borda,
        test_parametros_invalidos,
        test_entrada_que_nao_e_binaria,
        test_falha_de_leitura,
        test_imagens_do_estudo,
    ]
    for teste in testes:
        teste()
        print(f"ok - {teste.__name__}")
    print(f"{len(testes)} testes passaram")
