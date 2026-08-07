from picamera2 import Picamera2
from PIL import Image, ImageDraw
import numpy as np
import time

# =====================================================
# CONFIGURAÇÃO
# =====================================================

picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (320, 240), "format": "RGB888"}
)
picam2.configure(config)
picam2.set_controls({"AeEnable": True, "AwbEnable": True})
picam2.start()

LARGURA = 320
ALTURA = 240
MIN_DIAMETRO = int(LARGURA * 0.10)  # 10% = 32 pixels
MIN_AREA = 3.14159 * (MIN_DIAMETRO/2)**2  # ~804 pixels

print(f"Detectando bolas com diâmetro >= {MIN_DIAMETRO} pixels")
print("=" * 50)

# =====================================================
# LOOP PRINCIPAL
# =====================================================

while True:
    
    # Capturar imagem
    frame = picam2.capture_array()
    frame_rgb = frame[:, :, ::-1]
    
    # Canais
    r = frame_rgb[:, :, 0].astype(np.float32)
    g = frame_rgb[:, :, 1].astype(np.float32)
    b = frame_rgb[:, :, 2].astype(np.float32)
    
    # Detectar cores
    vermelho = (r > g * 2.4) & (r > b * 2.4) & (r > 60)
    verde = (g > r * 2.4) & (g > b * 2.4) & (g > 60)
    azul = (b > r * 2.4) & (b > g * 2.4) & (b > 60)
    amarelo = (r > 80) & (g > 80) & (b < 60)
    
    # Imagem de saída
    saida = frame_rgb.copy()
    mensagens = []
    
    # Função para processar cada cor
    def processar_cor(mascara, nome, cor_bgr):
        ys, xs = np.where(mascara)
        if len(xs) < MIN_AREA * 0.5:
            return
        
        # Verificar tamanho
        largura = np.max(xs) - np.min(xs)
        altura = np.max(ys) - np.min(ys)
        diametro = max(largura, altura)
        
        if diametro >= MIN_DIAMETRO:
            x, y = int(np.mean(xs)), int(np.mean(ys))
            mensagens.append(f"{nome}({x},{y})")
            
            # Desenhar círculo
            raio = diametro // 2
            for angulo in range(0, 360, 20):
                import math
                rad = math.radians(angulo)
                xx = int(x + raio * math.cos(rad))
                yy = int(y + raio * math.sin(rad))
                if 0 <= xx < LARGURA and 0 <= yy < ALTURA:
                    saida[yy, xx] = cor_bgr
            
            # Centro
            saida[y-5:y+6, x-5:x+6] = cor_bgr
    
    # Processar todas as cores
    processar_cor(vermelho, "VERMELHA", (0, 0, 255))
    processar_cor(verde, "VERDE", (0, 255, 0))
    processar_cor(azul, "AZUL", (255, 0, 0))
    processar_cor(amarelo, "AMARELA", (0, 255, 255))
    
    # Adicionar texto
    img_saida = Image.fromarray(saida.astype(np.uint8))
    draw = ImageDraw.Draw(img_saida)
    
    if mensagens:
        texto = " | ".join(mensagens)
        print(f"\r{texto}                    ", end="")
        draw.text((10, 10), f"BOLAS: {texto}", fill=(0, 255, 0))
    else:
        print(f"\rNenhuma bola grande detectada...", end="")
        draw.text((10, 10), "Nenhuma bola grande detectada", fill=(255, 255, 255))
    
    draw.text((10, 30), f"Minimo: {MIN_DIAMETRO}px diametro", fill=(255, 255, 255))
    
    # Salvar
    img_saida.save("/bats/fotos/ramdisk/saida.jpg", quality=90)
    
    time.sleep(0.1)