Laboratório M2.1 - máscara binária e segmentação.
Linguagem: python.

Dependências: opencv-python e numpy, estão no requirements.txt.

É necessário fazer pip install das dependencias:

python -m venv .venv
python -m pip install -r requirements.txt

Não tem compilação, python é interpretado.

Execução do código deverá ser feita fazendo:

python src/pdi_lab/main.py --input <arquivo> --output <arquivo> --operation segment --method <metodo> [opcoes]

--method aceita fixed, otsu, adaptive e hsv.

parâmetros de cada método:
fixed     --threshold (0 a 255), obrigatório
otsu      nenhum, o limiar sai do histograma
adaptive  --block-size (ímpar, >= 3) e --constant
hsv       --hmin --hmax (0 a 179) --smin --smax --vmin --vmax (0 a 255)

parâmetros que valem para todos:
--blur     tamanho do GaussianBlur do pré-processamento, 0 desliga (precisa ser ímpar)
--invert   inverte a máscara no final, para quando o objeto é mais escuro que o fundo
--overlay  caminho opcional para salvar a sobreposição da máscara em cima da original

A máscara sai sempre em png, com um canal e só com os valores 0 (fundo) e 255 (objeto).

imagens usadas no estudo:
images/input/catdonut.jpg        - caso que funciona, 6 objetos separados sobre a mesa (5 rosquinhas e o gato)
images/input/gato_uva.png        - caso intermediário, muitas uvas encostadas umas nas outras
images/input/gato_chinchilla.png - caso que falha, bicho cinza sobre juta bege com muita textura

as outras imagens da pasta images/input foram testadas também, mas não entraram no relatório.

comandos das duas configurações comparadas em cada imagem:

python src/pdi_lab/main.py --input images/input/catdonut.jpg --output images/output/donut_fixed_150.png --operation segment --method fixed --threshold 150 --blur 5 --overlay images/output/donut_fixed_150_overlay.png
python src/pdi_lab/main.py --input images/input/catdonut.jpg --output images/output/donut_hsv_s120.png --operation segment --method hsv --smin 120 --blur 5 --overlay images/output/donut_hsv_s120_overlay.png

python src/pdi_lab/main.py --input images/input/gato_uva.png --output images/output/uva_fixed_150.png --operation segment --method fixed --threshold 150 --blur 5 --overlay images/output/uva_fixed_150_overlay.png
python src/pdi_lab/main.py --input images/input/gato_uva.png --output images/output/uva_hsv_verde.png --operation segment --method hsv --hmin 30 --hmax 85 --smin 80 --blur 5 --overlay images/output/uva_hsv_verde_overlay.png

python src/pdi_lab/main.py --input images/input/gato_chinchilla.png --output images/output/chinchilla_fixed_120.png --operation segment --method fixed --threshold 120 --blur 5 --invert --overlay images/output/chinchilla_fixed_120_overlay.png
python src/pdi_lab/main.py --input images/input/gato_chinchilla.png --output images/output/chinchilla_hsv_smax40.png --operation segment --method hsv --smax 40 --blur 5 --overlay images/output/chinchilla_hsv_smax40_overlay.png

o Otsu que eu rodei em cada imagem, só para comparar:

python src/pdi_lab/main.py --input images/input/catdonut.jpg --output images/output/donut_otsu.png --operation segment --method otsu --blur 5
python src/pdi_lab/main.py --input images/input/gato_uva.png --output images/output/uva_otsu.png --operation segment --method otsu --blur 5
python src/pdi_lab/main.py --input images/input/gato_chinchilla.png --output images/output/chinchilla_otsu.png --operation segment --method otsu --blur 5 --invert

as máscaras escolhidas para o M2.2 são:
images/output/donut_hsv_s120.png
images/output/uva_hsv_verde.png
images/output/chinchilla_hsv_smax40.png

testes:

python -m pytest

ou, se não tiver o pytest instalado, dá pra rodar o arquivo direto:

python tests/test_segment.py

os testes escrevem os arquivos deles em tests/saida.

códigos de saída: 0 quando dá certo, diferente de 0 quando dá erro (arquivo que não abre, método desconhecido, parâmetro inválido).
