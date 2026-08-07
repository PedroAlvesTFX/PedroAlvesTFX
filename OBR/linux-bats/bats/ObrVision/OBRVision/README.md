# OBR Vision

Sistema de visão (Raspberry Pi Zero 2W) pro robô da OBR (Olimpíada
Brasileira de Robótica): segue linha, detecta verde/vermelho/
obstáculo/área de resgate, e manda tudo pro ESP32 via UART em JSON.
Tem um dashboard web pra calibrar sem precisar mexer em código.

## Estrutura

```
OBRVision/
├── main.py            <- ponto de entrada
├── camera.py           <- captura continua (thread propria), rotaciona no hardware
├── vision.py            <- "cerebro": corrige iluminacao, chama detectores, guarda resultado
├── uart.py               <- envia JSON compacto pro ESP32
├── server.py               <- dashboard web (Flask): stream MJPEG + sliders + status
├── config.py                <- le/escreve config/hsv.json, thread-safe
├── detectors/
│   ├── line.py                <- segue linha (ROI inferior, preto por V+S)
│   ├── red.py                  <- vermelho perto (distancia via regressao Y->mm)
│   ├── green.py                  <- verde (esquerda/direita/ambos/nenhum)
│   └── obstacle.py                <- blob escuro largo fora da faixa da linha
├── config/hsv.json                  <- todos os thresholds calibraveis
├── templates/index.html
└── static/{style.css,script.js}
```

## Como roda (visão geral)

```
Camera (thread)                    Vision loop (thread)                Flask (main thread)
   |                                    |                                    |
captura continua              le ultimo frame disponivel          serve dashboard
guarda so o ultimo frame  -->  corrige iluminacao                 stream MJPEG (le
                                converte HSV                        ultimo debug_frame
                                roda detectores ativos               calculado)
                                (conforme o estado da missao)
                                atualiza objects + debug_frames    le objects pra /api/status
                                        |
                                  UartSender.send() -- manda JSON pro ESP32
```

Três coisas nunca se bloqueiam entre si: a câmera sempre captura no
próprio ritmo, o processamento sempre usa o frame mais recente
disponível (nunca acumula fila), e a página web só lê o que já foi
calculado (travar o navegador não afeta o robô).

## Instalação (Raspberry Pi OS, Bookworm+)

`picamera2` e `libcamera` **não vêm pelo pip** -- são pacotes de
sistema (dependem de bibliotecas nativas específicas do Pi). Se você
já tem tudo funcionando como disse, pode pular direto pro `pip
install -r requirements.txt`. Se precisar do zero:

```bash
sudo apt update
sudo apt install -y python3-picamera2 python3-libcamera python3-opencv
python3 -m venv --system-site-packages venv   # --system-site-packages: pra enxergar picamera2/libcamera do apt
source venv/bin/activate
pip install -r requirements.txt
```

Habilite a UART do Pi (`raspi-config` -> Interface Options -> Serial
Port -> desabilita o console serial, habilita a porta de hardware) --
sem isso `/dev/serial0` não existe.

## Rodando

```bash
python3 main.py
```

Acesse `http://<ip-do-pi>:8000/` -- abas Original/Preto/Verde/
Vermelho/HSV pra ver cada máscara ao vivo, sliders por detector, e
os botões **Salvar** (grava em `config/hsv.json`) e **Descartar e
recarregar** (volta pro que já estava salvo, joga fora ajustes não
salvos).

## Calibrando

1. Escolhe a aba da cor que quer calibrar (ex.: Preto, pra linha).
2. Mexe nos sliders daquele detector até a máscara mostrar só o que
   deveria (linha em branco, resto em preto).
3. `min_area` filtra ruído pequeno -- suba até sumir o "granulado"
   sem apagar o objeto real.
4. **Vermelho:** a distância (`redDistance`) depende dos
   `calib_points` em `config/hsv.json` (posição Y do centro do
   vermelho na imagem x distância real em mm, medida com a câmera
   fixa na posição final). Recalibrar = remedir 2-3 pontos com uma
   régua e atualizar esses valores no JSON diretamente (não tem
   slider pra isso ainda).
5. Aperta **Salvar** quando estiver bom -- sem isso, um restart do
   `main.py` volta pro último config salvo.

## Estados da missão

`vision.py` só roda os detectores relevantes pro estado atual
(`STATE_DETECTORS`) -- outros ficam parados, economizando CPU. Troca
de estado pelo dropdown do dashboard, ou programaticamente chamando
`vision.set_state("GREEN")` de outro lugar do seu código (ex.: se
depois você quiser automatizar a máquina de estados olhando o
próprio `objects` -- isso ainda não está implementado, é decisão sua
de estratégia).

## Protocolo UART

Uma linha JSON por mensagem, taxa configurável em
`config["uart"]["send_hz"]` (default 20 Hz):

```json
{"linePresent":true,"lineError":0.12,"lineAngle":-3.4,"green":"none","redPresent":false,"redDistance":null,"obstacle":false,"state":"FOLLOW_LINE","fps":24.1}
```

`lineError`: -1 (linha na extrema esquerda) a +1 (extrema direita).
`lineAngle`: graus, 0 = linha alinhada com a frente do robô.

## O que ainda é ponto de partida, não solução pronta

- **`obstacle.py`**: o documento original não detalhava o algoritmo
  (só a necessidade) -- implementei detecção de blob escuro largo
  fora da faixa da linha, mas isso depende muito do layout real dos
  obstáculos da categoria. Espere recalibrar/ajustar a lógica em
  cima da pista de verdade.
- **Calibração automática de 4 padrões** (branco/preto/vermelho/
  verde na primeira inicialização), mencionada como ideia futura no
  documento original -- não implementada ainda; hoje a calibração é
  manual via sliders.
- **Máquina de estados automática**: o dashboard deixa trocar de
  estado manualmente; decidir sozinho quando trocar (ex.: "achei
  verde, mudar pra estado GREEN") é lógica de estratégia que fica a
  seu critério implementar (provavelmente no próprio `vision_loop`
  de `main.py`, olhando `objects` a cada frame).
