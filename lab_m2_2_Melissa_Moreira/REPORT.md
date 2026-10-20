Nome: Melissa Moreira de Oliveira.

SEÇÃO M2.1 (relatório da entrega anterior, mantido)

Objetivo: fazer a máscara binária dos objetos em três imagens, comparar duas configurações na mesma imagem e escolher qual máscara vai para o M2.2.

Alvo: o objeto de interesse é o que está em cima do fundo. Nas rosquinhas são as 5 rosquinhas e o gato enrolado no meio delas, nas uvas é o cacho (e as uvas soltas), e na última é o bicho cinza. O fundo é a mesa de madeira, o caixote com o fundo desfocado e o pano de juta.

Imagens: eu testei as 8 imagens da pasta images/input com os quatro métodos e escolhi três, uma de cada comportamento.
    - images/input/catdonut.jpg (880x728): caso que funciona. Foto de cima, iluminação parecida na imagem toda e 6 objetos separados, 5 rosquinhas e o gato. É a imagem com mais de um objeto, que o M2.2 precisa.
    - images/input/gato_uva.png (880x707): caso intermediário. A máscara acerta o cacho, mas as uvas se tocam, então elas não dão pra separar.
    - images/input/gato_chinchilla.png (880x838): caso que falha. O bicho é cinza e a juta é bege, os dois no mesmo nível de brilho, e a trama do pano é uma textura forte.
    Os originais não foram alterados, tudo que o programa gera vai para images/output.

Operações implementadas: a operação segment, com os métodos fixed, otsu, adaptive e hsv, mais a opção --overlay que salva a sobreposição da máscara na imagem original.

Decisões de implementação: linguagem python. Usei GaussianBlur 5x5 (--blur 5) nas duas configurações de cada imagem, para a comparação ser justa. Foi por causa da textura da madeira, da juta e do pelo, que sem suavizar enchem a máscara de pixels soltos. Na chinchilla usei --invert no limiar fixo, porque ali o bicho é mais escuro que o pano. Nos dois usos do hsv os limites estão na escala do OpenCV, H de 0 a 179 e S e V de 0 a 255.

Configurações comparadas:

| imagem | configuração | parâmetros | inversão |
|---|---|---|---|
| catdonut.jpg | fixed | --threshold 150 --blur 5 | não |
| catdonut.jpg | hsv | --smin 120, H de 0 a 179, V de 0 a 255, --blur 5 | não |
| gato_uva.png | fixed | --threshold 150 --blur 5 | não |
| gato_uva.png | hsv | --hmin 30 --hmax 85 --smin 80, --blur 5 | não |
| gato_chinchilla.png | fixed | --threshold 120 --blur 5 | sim |
| gato_chinchilla.png | hsv | --smax 40, H de 0 a 179, V de 0 a 255, --blur 5 | não |

No hsv da uva eu usei a faixa de matiz do verde (30 a 85). Como 30 é menor que 85, o intervalo não cruza a descontinuidade do matiz e não precisou ser quebrado em duas faixas. O programa trata esse caso quando --hmin é maior que --hmax. Nas outras duas eu não restringi o matiz, filtrei só pela saturação: na catdonut pegando o que é colorido (--smin 120) e na chinchilla pegando o que é sem cor (--smax 40), porque o bicho é cinza e a juta é bege.

Resultados (proporção de primeiro plano):

| imagem | configuração | pixels de objeto | total | proporção |
|---|---|---|---|---|
| catdonut.jpg | fixed 150 | 296208 | 640640 | 46,24% |
| catdonut.jpg | hsv smin 120 | 217596 | 640640 | 33,97% |
| catdonut.jpg | otsu (117) | 419695 | 640640 | 65,51% |
| gato_uva.png | fixed 150 | 364257 | 622160 | 58,55% |
| gato_uva.png | hsv verde | 291976 | 622160 | 46,93% |
| gato_uva.png | otsu (139) | 394029 | 622160 | 63,33% |
| gato_chinchilla.png | fixed 120 + invert | 253818 | 737440 | 34,42% |
| gato_chinchilla.png | hsv smax 40 | 159764 | 737440 | 21,66% |
| gato_chinchilla.png | otsu (110) + invert | 195423 | 737440 | 26,50% |

Figuras:
    Figura 1 - images/input/catdonut.jpg: original.
    Figura 2 - images/output/donut_fixed_150.png: máscara do limiar fixo 150.
    Figura 3 - images/output/donut_hsv_s120.png: máscara do hsv com saturação a partir de 120.
    Figura 4 - images/output/donut_hsv_s120_overlay.png: sobreposição da máscara escolhida, em vermelho o objeto e em amarelo o contorno.
    Figura 5 - images/output/donut_fixed_150_overlay.png: mesma sobreposição para o limiar fixo.
    Figura 6 - images/input/gato_uva.png: original do caso intermediário.
    Figura 7 - images/output/uva_fixed_150.png: máscara do limiar fixo 150.
    Figura 8 - images/output/uva_hsv_verde.png: máscara do hsv na faixa do verde.
    Figura 9 - images/output/uva_hsv_verde_overlay.png: sobreposição, dá pra ver que o cacho inteiro virou uma mancha só.
    Figura 10 - images/input/gato_chinchilla.png: original do caso que falha.
    Figura 11 - images/output/chinchilla_fixed_120.png: máscara do limiar fixo 120 invertido, a trama da juta vira ruído na imagem toda.
    Figura 12 - images/output/chinchilla_hsv_smax40.png: máscara do hsv com saturação até 40.
    Figura 13 - images/output/chinchilla_hsv_smax40_overlay.png: sobreposição, o bicho aparece mas cheio de furos.

Análise técnica:
    - catdonut.jpg: o limiar fixo não funciona. Não existe um nível de cinza que separe os objetos da madeira, porque a rosquinha de chocolate e a vermelha são mais escuras que a mesa e a de glacê branco é mais clara. O hsv funciona porque a madeira é acinzentada e os objetos são coloridos. Erros que sobram: a rosquinha de glacê branco quase não aparece, por ser clara e pouco saturada, e as ranhuras entre as tábuas entram como tiras finas, uma delas encostando na rosquinha verde e no gato.
    - gato_uva.png: aqui os dois métodos acertam mais ou menos a região das uvas, o limiar fixo porque elas são claras e o hsv porque elas são verdes. O hsv é melhor porque o fundo desfocado atrás do caixote também é claro e entra no limiar fixo. O problema dessa imagem não é a máscara, é que as uvas se encostam e a região delas vira uma mancha única. O hsv também pega um pedaço da folhagem desfocada no canto de cima, que é verde igual.
    - gato_chinchilla.png: nenhuma configuração funciona. A juta e o bicho têm quase o mesmo brilho, e a trama do pano tem contraste local, então o limiar fixo invertido espalha ruído pela imagem inteira. O hsv com --smax 40 é o menos ruim, porque o pano é bege (tem cor) e o bicho é cinza (quase sem cor), mas mesmo assim a máscara sai com o lombo e o rabo comidos e cheia de furos, e os restos de comida no chão entram junto.

Configurações escolhidas para o M2.2:
    - catdonut.jpg: hsv com --smin 120 (images/output/donut_hsv_s120.png).
    - gato_uva.png: hsv na faixa do verde (images/output/uva_hsv_verde.png).
    - gato_chinchilla.png: hsv com --smax 40 (images/output/chinchilla_hsv_smax40.png), que é a menos ruim das três que eu testei nessa imagem.

(a) Em que casos o limiar fixo falhou ou funcionou: ele chegou perto só na uva, que tem objeto claro em região mais escura, e mesmo assim trouxe o fundo desfocado junto. Falhou na catdonut, onde os objetos ficam dos dois lados do brilho da madeira, e falhou feio na chinchilla, onde o objeto e o fundo têm o mesmo brilho. Ou seja, o limiar fixo só resolve quando a separação é mesmo de intensidade.

(b) Qual parâmetro foi mais sensível: o parâmetro de saturação do hsv. Na catdonut, com --smin 80, 100, 120 e 130 o primeiro plano foi 44,56%, 38,04%, 33,97% e 32,11%: com 80 a madeira entra quase toda e as rosquinhas ficam grudadas, e de 120 pra cima a rosquinha branca some. Na chinchilla o --smax muda o resultado do mesmo jeito, porque o bege da juta e o cinza do bicho estão perto na saturação. O --threshold do limiar fixo foi bem menos sensível nas três.

(c) Quais erros podem atrapalhar a contagem no M2.2:
    - na catdonut, as tiras da madeira ligam uma rosquinha na outra, e a rosquinha branca está quebrada em pedaços;
    - na uva, as uvas se tocam, então muitos objetos viram um componente só;
    - na chinchilla, os furos no corpo do bicho podem partir ele em vários componentes, e os restos de comida no chão viram objetos que não interessam;
    - nas três, os pontinhos soltos do fundo viram componentes minúsculos e aumentam a contagem.

Testes realizados: estão em tests/test_segment.py e rodam com python -m pytest ou python tests/test_segment.py. São 7 testes: limiar fixo numa imagem sintética com pixels abaixo, em cima e acima do limiar (o cv2.threshold usa f > T, então o pixel igual ao limiar fica no fundo), o mesmo com --invert, as três imagens reais nas duas configurações de cada uma conferindo dimensão, canal único e valores {0, 255}, falha de leitura, método desconhecido, parâmetros inválidos e chamada sem --output. Erro sempre retorna código diferente de 0 e sucesso retorna 0.

Limitações: não tenho máscara de referência, então o que eu falei de acerto e erro é observação visual nas sobreposições. Por isso não dá pra falar em acurácia, precisão ou revocação. O único número medido é a contagem de pixels de primeiro plano, que está na tabela.

Declaração de uso ou não de IA:Uso de IA para gerar e rodar os testes(e para verificar corretude dos mesmos). Uso de IA para análise estática do código e verificação de corretude em relação aos requisitos pedidos (no contrato e na especificação, para verificar se esqueci algo), e em relação a pertinência do que eu escrevi.

Referências: slides disponíveis no AVA, arquivos .md passados pelo professor e a documentação do OpenCV das funções threshold, adaptiveThreshold e inRange.

----------------------------------------------------------------

SEÇÃO M2.2

Objetivo: pegar as máscaras do M2.1, limpar com uma sequência morfológica, rotular os componentes conexos, contar os objetos e comparar antes e depois.

Máscaras de partida: as três saíram do próprio projeto, pelos comandos do README.md. Nas três o objeto está em branco (255) e o fundo em preto (0), e o programa confere isso antes de analisar.
    results/donut_mask_initial.png é a cópia de images/output/donut_hsv_s120.png
    results/uva_mask_initial.png é a cópia de images/output/uva_hsv_verde.png
    results/chinchilla_mask_initial.png é a cópia de images/output/chinchilla_hsv_smax40.png

Rotulação da máscara inicial, mesma máscara e mesmos parâmetros, só mudando a conectividade:

| imagem | máscara inicial | componentes com conectividade 4 | componentes com conectividade 8 |
|---|---|---|---|
| catdonut.jpg | donut_hsv_s120.png | 103 | 82 |
| gato_uva.png | uva_hsv_verde.png | 58 | 34 |
| gato_chinchilla.png | chinchilla_hsv_smax40.png | 341 | 185 |

A conectividade 4 conta mais nas três. Ela só liga pixel que se toca pelo lado, e a 8 também liga os que se tocam pelo canto, então todo pedaço preso no vizinho apenas pela diagonal conta separado na 4 e junta na 8: 21 pedaços a mais na catdonut, 24 na uva e 156 na chinchilla. A diferença é maior justamente onde tem mais ruído: na chinchilla a trama da juta deixa a máscara cheia de respingos com borda serrilhada. Escolhi conectividade 8 na análise final porque ela é mais tolerante nas partes finas. Num objeto cheio a escolha não muda nada, o miolo dele está ligado pelo lado de qualquer jeito, mesmo que a borda seja inclinada. A diferença aparece onde a máscara tem fiapo de 1 ou 2 pixels, como a ponta de um respingo ou a serrilha da borda, que na conectividade 4 se parte em vários pedaços.

Sequência morfológica, igual nas três imagens, com elemento estruturante em elipse:

| estágio | operação | elemento | tamanho | iterações | problema que ataca |
|---|---|---|---|---|---|
| 1 | abertura (open) | elipse | 7x7 | 1 | tirar os respingos do fundo e as tiras finas (as ranhuras da madeira, a trama da juta) |
| 2 | fechamento (close) | elipse | 15x15 | 1 | fechar os buracos dentro dos objetos (granulados, brilho e falhas no pelo) |

A ordem importa. A abertura vem primeiro porque ela apaga o que é fino antes que o fechamento consolide esse ruído. O fechamento não engrossa um respingo isolado, já que ele dilata e depois erode e o respingo volta ao tamanho, mas ele cola respingos vizinhos e liga a tira de madeira nas rosquinhas, formando blocos largos que a abertura depois não tira mais. Eu rodei as duas ordens na catdonut: com a abertura primeiro sobraram 11 componentes brutos e 220329 pixels de primeiro plano, e com o fechamento primeiro sobraram 14 componentes brutos e 230005 pixels, ou seja, mais sujeira (as duas ordens terminam com 7 componentes acima de 500 pixels).

O tamanho 7x7 veio da espessura da tira de madeira: o componente 1 do csv inicial tem 1682 pixels distribuídos em 394 linhas, o que dá mais ou menos 4 px de espessura média, e a caixa dele tem 7 px de largura, que é o ponto mais largo. Um elemento de 7x7 apaga o que é mais fino que isso. O 15x15 é porque os buracos dentro das rosquinhas são maiores que o elemento da abertura. As duas operações têm finalidade diferente.

Efeito de cada estágio no primeiro plano:

| imagem | estágio | operação | pixels antes | pixels depois |
|---|---|---|---|---|
| catdonut.jpg | 1 | open 7x7 | 217596 | 208385 |
| catdonut.jpg | 2 | close 15x15 | 208385 | 220329 |
| gato_uva.png | 1 | open 7x7 | 291976 | 289604 |
| gato_uva.png | 2 | close 15x15 | 289604 | 303006 |
| gato_chinchilla.png | 1 | open 7x7 | 159764 | 149180 |
| gato_chinchilla.png | 2 | close 15x15 | 149180 | 163079 |

Critério de filtragem: --min-area 500. Componente com menos de 500 pixels sai da contagem, mas não é apagado da máscara, ele entra no csv com kept=false. Escolhi 500 porque o menor objeto que me interessa tem mais de 2000 pixels e o ruído de fundo fica quase todo abaixo de 400. Usei o mesmo valor nas três imagens e nas duas etapas. O rótulo 0 (fundo) nunca entra na contagem.

Resultados, tabela antes/depois:

| imagem | etapa | componentes brutos | componentes com área >= 500 | área total do primeiro plano |
|---|---|---|---|---|
| catdonut.jpg | inicial | 82 | 7 | 217596 |
| catdonut.jpg | final | 11 | 7 | 220329 |
| gato_uva.png | inicial | 34 | 4 | 291976 |
| gato_uva.png | final | 4 | 3 | 303006 |
| gato_chinchilla.png | inicial | 185 | 4 | 159764 |
| gato_chinchilla.png | final | 14 | 3 | 163079 |

Observações, catdonut.jpg (o caso que funciona):
    1. a contagem bruta caiu de 82 para 23 logo depois da abertura e terminou em 11 depois do fechamento. O que sumiu na abertura era quase tudo respingo da madeira, e o fechamento ainda juntou alguns pedaços vizinhos;
    2. a área total subiu 1,25%, mesmo a abertura tendo tirado 9211 pixels, porque o fechamento devolveu mais do que isso fechando buracos;
    3. o componente 2 da máscara inicial tinha 86391 pixels e caixa de 265x684, ou seja, a rosquinha verde e o gato estavam grudados por uma tira de madeira. Já na saída da abertura eles aparecem separados, com 33614 e 49441 pixels, e terminam a sequência com 38873 e 50576 pixels, depois do fechamento. Foi aqui que a sequência ajudou;
    4. a tira de madeira tinha 1682 pixels, então passava sozinha no filtro de área. A abertura cortou quase toda ela, mas sobrou um pedaço de 192 pixels (componente 6 do donut_final.csv), que aí sim o filtro de 500 descartou. Quem resolveu foram as duas coisas juntas: a abertura olhando a forma e o filtro olhando o tamanho.

Observações, gato_uva.png (o caso intermediário):
    1. a máscara está boa e a contagem está errada: as uvas se tocam, então o cacho inteiro é um componente só, de 283686 pixels, com caixa de 604x707. Na foto dá pra contar mais ou menos 30 uvas;
    2. a abertura quase não mudou nada aqui (291976 para 289604), porque o contato entre as uvas é largo, não é uma ponte fina como a tira de madeira;
    3. por isso eu testei uma abertura bem maior, 31x31, no comando results/uva_open31 do README. Ela tirou 27010 pixels e mesmo assim o cacho continuou um componente de 262524 pixels. Morfologia não separa objetos que se encostam numa área grande, só corta ligação fina. Para isso precisaria de watershed, que o enunciado deixa como extensão opcional;
    4. o que a contagem acerta são as uvas soltas na quina de baixo: elas ficaram em componentes separados, de 16774 e 2454 pixels.

Observações, gato_chinchilla.png (o caso que falha):
    1. a máscara inicial tinha 185 componentes, quase tudo respingo da juta. A abertura derrubou para 39, o fechamento juntou pedaços vizinhos e fechou em 14, e o filtro de área deixou 3;
    2. os 3 que sobraram são o bicho (157359 pixels) e dois restos de comida no chão (1014 e 2569 pixels). Ou seja, a contagem "3" mistura o objeto que interessa com sujeira que passou no filtro;
    3. o componente do bicho está cheio de furos e com o lombo e o rabo comidos, porque ali o cinza do pelo tem saturação parecida com a do pano. O fechamento devolveu 13899 pixels, mas não recuperou a forma;
    4. aqui a sequência melhora o número e não melhora o resultado: a máscara continua ruim, só fica mais limpa de respingo.

Figuras:
    Figura 14 - results/donut_mask_initial.png: máscara inicial da catdonut.jpg.
    Figura 15 - results/donut_stage1_open.png: depois da abertura 7x7, os respingos da madeira sumiram e a tira entre a rosquinha verde e o gato foi cortada, sobrando um pedaço de 192 px que o filtro de área descarta.
    Figura 16 - results/donut_stage2_close.png: depois do fechamento 15x15, os buracos diminuíram.
    Figura 17 - results/donut_labels.png: componentes finais coloridos por rótulo, com caixa e número nos que passaram no filtro.
    Figura 18 - results/uva_mask_initial.png: máscara inicial da gato_uva.png, o cacho já é uma mancha só.
    Figura 19 - results/uva_stage1_open.png: depois da abertura, praticamente igual.
    Figura 20 - results/uva_labels.png: um componente para o cacho inteiro e dois para as uvas soltas.
    Figura 21 - results/uva_open31_mask_final.png: tentativa com abertura 31x31, o cacho continua inteiro.
    Figura 22 - results/chinchilla_mask_initial.png: máscara inicial da gato_chinchilla.png, cheia de respingo.
    Figura 23 - results/chinchilla_stage1_open.png: depois da abertura, o respingo sai e os furos ficam.
    Figura 24 - results/chinchilla_labels.png: o bicho e dois restos de comida.

Componentes finais que passaram no filtro:

| imagem | rótulo | área | caixa (x, y, w, h) | o que é na foto |
|---|---|---|---|---|
| catdonut.jpg | 1 | 42469 | 618, 54, 241, 256 | rosquinha amarela |
| catdonut.jpg | 2 | 38279 | 13, 59, 250, 265 | rosquinha de chocolate |
| catdonut.jpg | 3 | 38873 | 332, 64, 261, 248 | rosquinha verde |
| catdonut.jpg | 7 | 40858 | 637, 379, 243, 259 | rosquinha vermelha |
| catdonut.jpg | 8 | 50576 | 333, 390, 263, 260 | o gato |
| catdonut.jpg | 10 e 11 | 3320 e 5636 | 96, 483, 79, 67 e 107, 489, 182, 157 | dois pedaços da rosquinha de glacê branco |
| gato_uva.png | 1 | 283686 | 276, 0, 604, 707 | o cacho inteiro, com mais ou menos 30 uvas |
| gato_uva.png | 3 | 2454 | 71, 378, 72, 75 | uma uva solta |
| gato_uva.png | 4 | 16774 | 0, 495, 179, 194 | as duas uvas soltas da quina, grudadas |
| gato_chinchilla.png | 1 | 157359 | 133, 187, 732, 489 | o bicho, com furos |
| gato_chinchilla.png | 7 e 8 | 1014 e 2569 | 261, 565, 48, 36 e 211, 617, 120, 74 | restos de comida no chão |

A contagem não bate com a interpretação humana em nenhuma das três, e na catdonut ela chega perto: deu 7 componentes para 6 objetos reais (5 rosquinhas e o gato). Cinco componentes estão certos, um por objeto, e a rosquinha de glacê branco é a que sobra, contada duas vezes porque ficou partida em dois pedaços e nenhum deles corresponde a ela inteira. Na uva a contagem dá 3 para mais ou menos 33 uvas, e na chinchilla dá 3 para um bicho e duas sujeiras. Componente conexo não é objeto: dois objetos que se tocam viram um, um objeto mal segmentado vira vários, e o que não interessa também entra se tiver área suficiente. O programa não tem como saber qual dos casos aconteceu.

Análise técnica, onde a sequência ajuda e onde atrapalha:
    - ajuda: na catdonut ela separou a rosquinha verde do gato e limpou 71 componentes de ruído, e na chinchilla ela derrubou 171 respingos da juta;
    - atrapalha: o fechamento arredonda o contorno e fecha buracos que existem na foto, então a área de cada componente fica maior que a do objeto. Nas três imagens a área total subiu depois da sequência;
    - não resolve: na uva ela não separa as uvas, nem com elemento 31x31, porque elas se encostam numa área larga. E na chinchilla ela não recupera o lombo e o rabo que a segmentação perdeu, porque morfologia mexe em forma e tamanho, não em cor. Esses dois erros vêm da etapa anterior.

Testes realizados: tests/test_segment.py continua com os 7 testes do M2.1, porque a operação segment ainda funciona, e tests/test_analyze.py tem mais 9. Os do analyze cobrem: máscara sintética com dois pixels na diagonal, que dá 2 componentes na conectividade 4 e 1 na 8; quadrado com três ruídos isolados, conferindo que a abertura tirou os ruídos e sobrou 1 componente; quadrado com furo de 4x4, conferindo que o fechamento 9x9 fechou o furo; máscara vazia, com contagem zero e csv só com o cabeçalho; objeto tocando a borda, que aparece no csv com x=0 e y=0; parâmetros inválidos (conectividade 6, área mínima negativa, sequência com uma operação só, operação que não existe, elemento de tamanho par e quantidade de tamanhos diferente da de operações); máscara que não é binária; falha de leitura; e as três imagens do estudo, do segment até o analyze, conferindo que a soma das áreas dos componentes brutos é igual à quantidade de pixels de primeiro plano da máscara, antes do filtro.

Limitações: continuo sem máscara de referência e sem contagem manual documentada, então aqui eu comparo contagem de componentes, área em pixels e o que dá pra ver nas figuras. O número de uvas que eu cito é estimativa minha olhando a foto, não é medida. Não calculei acurácia.

Declaração de uso ou não de IA:Uso de IA para gerar e rodar os testes(e para verificar corretude dos mesmos). Uso de IA para análise estática do código e verificação de corretude em relação aos requisitos pedidos (no contrato e na especificação, para verificar se esqueci algo), e em relação a pertinência do que eu escrevi.

Referências: slides disponíveis no AVA, arquivos .md passados pelo professor e a documentação do OpenCV das funções connectedComponentsWithStats, morphologyEx e getStructuringElement.
