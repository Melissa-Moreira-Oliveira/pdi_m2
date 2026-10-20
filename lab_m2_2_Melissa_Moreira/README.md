Laboratório M2.2 - componentes conexos e sequência morfológica.
É o mesmo projeto do M2.1, com a operação segment ainda funcionando e a operação analyze a mais.
Linguagem: python.

Dependências: opencv-python e numpy, estão no requirements.txt.

É necessário fazer pip install das dependencias:

python -m venv .venv
python -m pip install -r requirements.txt

Não tem compilação, python é interpretado.

Execução do código deverá ser feita fazendo:

python src/pdi_lab/main.py --input <arquivo> --output <arquivo-ou-prefixo> --operation <segment|analyze> [opcoes]

OPERAÇÃO SEGMENT (a mesma do M2.1)

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

imagens do estudo:
images/input/catdonut.jpg        - caso que funciona, 6 objetos separados (5 rosquinhas e o gato)
images/input/gato_uva.png        - caso intermediário, uvas encostadas umas nas outras
images/input/gato_chinchilla.png - caso que falha, bicho cinza sobre juta bege

comandos para reproduzir as máscaras do M2.1:

python src/pdi_lab/main.py --input images/input/catdonut.jpg --output images/output/donut_fixed_150.png --operation segment --method fixed --threshold 150 --blur 5 --overlay images/output/donut_fixed_150_overlay.png
python src/pdi_lab/main.py --input images/input/catdonut.jpg --output images/output/donut_hsv_s120.png --operation segment --method hsv --smin 120 --blur 5 --overlay images/output/donut_hsv_s120_overlay.png

python src/pdi_lab/main.py --input images/input/gato_uva.png --output images/output/uva_fixed_150.png --operation segment --method fixed --threshold 150 --blur 5 --overlay images/output/uva_fixed_150_overlay.png
python src/pdi_lab/main.py --input images/input/gato_uva.png --output images/output/uva_hsv_verde.png --operation segment --method hsv --hmin 30 --hmax 85 --smin 80 --blur 5 --overlay images/output/uva_hsv_verde_overlay.png

python src/pdi_lab/main.py --input images/input/gato_chinchilla.png --output images/output/chinchilla_fixed_120.png --operation segment --method fixed --threshold 120 --blur 5 --invert --overlay images/output/chinchilla_fixed_120_overlay.png
python src/pdi_lab/main.py --input images/input/gato_chinchilla.png --output images/output/chinchilla_hsv_smax40.png --operation segment --method hsv --smax 40 --blur 5 --overlay images/output/chinchilla_hsv_smax40_overlay.png

o Otsu de cada imagem, que eu rodei só para comparar:

python src/pdi_lab/main.py --input images/input/catdonut.jpg --output images/output/donut_otsu.png --operation segment --method otsu --blur 5
python src/pdi_lab/main.py --input images/input/gato_uva.png --output images/output/uva_otsu.png --operation segment --method otsu --blur 5
python src/pdi_lab/main.py --input images/input/gato_chinchilla.png --output images/output/chinchilla_otsu.png --operation segment --method otsu --blur 5 --invert

OPERAÇÃO ANALYZE

no analyze o --input é uma máscara binária (1 canal, só 0 e 255) e o --output é um prefixo de arquivos.

parâmetros:
--connectivity   4 ou 8, o padrão é 8
--min-area       inteiro não negativo, o padrão é 0 (sem filtro). O csv marca na coluna kept se o componente passou
--sequence       operações morfológicas separadas por vírgula, o padrão é open,close. Aceita open, close, erode e dilate, precisa de pelo menos duas e de pelo menos uma abertura ou fechamento
--kernel-sizes   um tamanho ímpar para cada operação da sequência, o padrão é 7,15
--iterations     um número de iterações para cada operação da sequência, o padrão é 1,1
--kernel-shape   ellipse, rect ou cross, o padrão é ellipse

a sequência inteira vem por linha de comando, não precisa editar o código para rodar outro caso.

arquivos que o analyze gera, com o prefixo <p>:
<p>_mask_initial.png   cópia da máscara inicial, antes de qualquer operação
<p>_stage1_open.png    saída do primeiro estágio da sequência (o nome tem o número e a operação)
<p>_stage2_close.png   saída do segundo estágio
<p>_mask_final.png     máscara depois da sequência inteira
<p>_initial.csv        componentes da máscara inicial
<p>_final.csv          componentes da máscara final
<p>_labels.png         componentes da máscara final coloridos, com caixa e número nos que passaram no filtro
<p>_summary.json       conectividade, parâmetros da sequência, contagens brutas e filtradas e áreas totais

o csv tem o formato label,area,x,y,width,height,cx,cy,kept e o fundo (rótulo 0) não entra nele.

comandos do estudo do M2.2:

python src/pdi_lab/main.py --input images/output/donut_hsv_s120.png --output results/donut --operation analyze --connectivity 8 --min-area 500 --sequence open,close --kernel-sizes 7,15 --iterations 1,1 --kernel-shape ellipse
python src/pdi_lab/main.py --input images/output/uva_hsv_verde.png --output results/uva --operation analyze --connectivity 8 --min-area 500 --sequence open,close --kernel-sizes 7,15 --iterations 1,1 --kernel-shape ellipse
python src/pdi_lab/main.py --input images/output/chinchilla_hsv_smax40.png --output results/chinchilla --operation analyze --connectivity 8 --min-area 500 --sequence open,close --kernel-sizes 7,15 --iterations 1,1 --kernel-shape ellipse

a tentativa de separar as uvas com uma abertura bem maior (está no relatório, não deu certo):

python src/pdi_lab/main.py --input images/output/uva_hsv_verde.png --output results/uva_open31 --operation analyze --connectivity 8 --min-area 500 --sequence open,close --kernel-sizes 31,15 --iterations 1,1 --kernel-shape ellipse

para ver a diferença entre as conectividades na mesma máscara é só trocar o --connectivity 8 por --connectivity 4 (as duas contagens já aparecem na tela nas duas vezes).

testes:

python -m pytest

ou, se não tiver o pytest instalado, dá pra rodar os arquivos direto:

python tests/test_segment.py
python tests/test_analyze.py

os testes escrevem os arquivos deles em tests/saida.

códigos de saída: 0 quando dá certo, diferente de 0 quando dá erro (arquivo que não abre, máscara que não é binária, conectividade inválida, área mínima negativa, sequência ou elemento estruturante inválidos).
