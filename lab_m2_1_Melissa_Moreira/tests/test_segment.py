import os
import sys
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

def le_mascara(nome):
    return cv2.imread(os.path.join(PROJETO, nome), cv2.IMREAD_GRAYSCALE)

def monta_imagem_sintetica(nome, valores):
    # imagem pequena em cinza, salva em png para não perder os valores
    matriz = np.array(valores, dtype=np.uint8)
    cv2.imwrite(os.path.join(PROJETO, nome), matriz)
    return nome

def eh_binaria(mascara):
    for valor in np.unique(mascara):
        if valor != 0 and valor != 255:
            return False
    return True

def test_limiar_fixo_em_imagem_sintetica():
    # o cv2.threshold usa f > T, então o pixel igual ao limiar fica no fundo
    entrada = monta_imagem_sintetica(caminho("sintetica_limiar.png"), [
        [100, 119, 120, 121, 200],
        [0, 60, 120, 180, 255],
    ])
    saida = caminho("sintetica_limiar_mask.png")
    resultado = roda("--input", entrada, "--output", saida,
                     "--operation", "segment", "--method", "fixed", "--threshold", "120")
    assert resultado.returncode == 0

    mascara = le_mascara(saida)
    esperado = np.array([
        [0, 0, 0, 255, 255],
        [0, 0, 0, 255, 255],
    ], dtype=np.uint8)
    assert np.array_equal(mascara, esperado)

def test_limiar_fixo_com_inversao():
    entrada = monta_imagem_sintetica(caminho("sintetica_limiar.png"), [
        [100, 119, 120, 121, 200],
        [0, 60, 120, 180, 255],
    ])
    saida = caminho("sintetica_limiar_inv_mask.png")
    resultado = roda("--input", entrada, "--output", saida, "--operation", "segment",
                     "--method", "fixed", "--threshold", "120", "--invert")
    assert resultado.returncode == 0

    mascara = le_mascara(saida)
    esperado = np.array([
        [255, 255, 255, 0, 0],
        [255, 255, 255, 0, 0],
    ], dtype=np.uint8)
    assert np.array_equal(mascara, esperado)

def test_imagens_reais_nas_duas_configuracoes():
    # as duas imagens do estudo, cada uma nas duas configurações comparadas
    casos = [
        ("images/input/catdonut.jpg", "donut_fixed",
         ["--method", "fixed", "--threshold", "150", "--blur", "5"]),
        ("images/input/catdonut.jpg", "donut_hsv",
         ["--method", "hsv", "--smin", "120", "--blur", "5"]),
        ("images/input/gato_uva.png", "uva_fixed",
         ["--method", "fixed", "--threshold", "150", "--blur", "5"]),
        ("images/input/gato_uva.png", "uva_hsv",
         ["--method", "hsv", "--hmin", "30", "--hmax", "85", "--smin", "80", "--blur", "5"]),
        ("images/input/gato_chinchilla.png", "chinchilla_fixed",
         ["--method", "fixed", "--threshold", "120", "--blur", "5", "--invert"]),
        ("images/input/gato_chinchilla.png", "chinchilla_hsv",
         ["--method", "hsv", "--smax", "40", "--blur", "5"]),
    ]
    for entrada, nome, parametros in casos:
        saida = caminho(nome + "_mask.png")
        resultado = roda("--input", entrada, "--output", saida, "--operation", "segment", *parametros)
        assert resultado.returncode == 0

        original = cv2.imread(os.path.join(PROJETO, entrada))
        mascara = le_mascara(saida)
        # dimensões, canal único e conjunto de valores {0, 255}
        assert len(mascara.shape) == 2
        assert mascara.shape[0] == original.shape[0]
        assert mascara.shape[1] == original.shape[1]
        assert eh_binaria(mascara)
        assert np.count_nonzero(mascara) > 0

def test_falha_de_leitura():
    resultado = roda("--input", "images/input/nao_existe.png", "--output", caminho("nada.png"),
                     "--operation", "segment", "--method", "otsu")
    assert resultado.returncode != 0

def test_metodo_desconhecido():
    resultado = roda("--input", "images/input/catdonut.jpg", "--output", caminho("nada.png"),
                     "--operation", "segment", "--method", "magico")
    assert resultado.returncode != 0

def test_parametros_invalidos():
    # limiar fora do intervalo, limiar faltando e blur par
    resultado = roda("--input", "images/input/catdonut.jpg", "--output", caminho("nada.png"),
                     "--operation", "segment", "--method", "fixed", "--threshold", "300")
    assert resultado.returncode != 0

    resultado = roda("--input", "images/input/catdonut.jpg", "--output", caminho("nada.png"),
                     "--operation", "segment", "--method", "fixed")
    assert resultado.returncode != 0

    resultado = roda("--input", "images/input/catdonut.jpg", "--output", caminho("nada.png"),
                     "--operation", "segment", "--method", "otsu", "--blur", "4")
    assert resultado.returncode != 0

    resultado = roda("--input", "images/input/catdonut.jpg", "--output", caminho("nada.png"),
                     "--operation", "segment", "--method", "hsv", "--smin", "200", "--smax", "100")
    assert resultado.returncode != 0

def test_saida_sem_output():
    resultado = roda("--input", "images/input/catdonut.jpg", "--operation", "segment", "--method", "otsu")
    assert resultado.returncode != 0

if __name__ == "__main__":
    testes = [
        test_limiar_fixo_em_imagem_sintetica,
        test_limiar_fixo_com_inversao,
        test_imagens_reais_nas_duas_configuracoes,
        test_falha_de_leitura,
        test_metodo_desconhecido,
        test_parametros_invalidos,
        test_saida_sem_output,
    ]
    for teste in testes:
        teste()
        print(f"ok - {teste.__name__}")
    print(f"{len(testes)} testes passaram")
