Nome: Melissa Moreira de Oliveira.

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
