#!/usr/bin/env python3
"""
Sistema de calibração de cores para ESP32-CAM
Referência: cartão com quadrados RGB + Preto + Branco
"""

import cv2
import numpy as np
from PIL import Image
import json
import os

class ColorCalibrator:
    def __init__(self):
        # Cores de referência (valores reais esperados)
        self.cores_referencia = {
            'preto': (0, 0, 0),
            'azul': (0, 0, 255),
            'verde': (0, 255, 0),
            'vermelho': (255, 0, 0),
            'branco': (255, 255, 255),
        }
        
        # Cores detectadas (valores medidos na imagem)
        self.cores_detectadas = {}
        
        # Matriz de correção
        self.matriz_correcao = None
        
    def detectar_quadrados(self, imagem_path):
        """
        Detecta automaticamente os quadrados coloridos na imagem de referência
        Usa thresholding e contornos para encontrar os retângulos
        """
        # Carrega imagem
        img = cv2.imread(imagem_path)
        if img is None:
            print(f"❌ Não foi possível carregar: {imagem_path}")
            return False
        
        # Converte para escala de cinza para encontrar contornos
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)
        
        # Encontra contornos
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filtra quadrados (contornos com 4 vértices e área razoável)
        quadrados = []
        for contour in contours:
            approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
            if len(approx) == 4:  # É um quadrilátero
                area = cv2.contourArea(contour)
                if area > 100:  # Ignora áreas muito pequenas
                    quadrados.append((approx, area))
        
        # Ordena quadrados por posição (da esquerda para direita, cima para baixo)
        quadrados.sort(key=lambda x: (x[0][0][0][1], x[0][0][0][0]))
        
        # Mapeia cores para os quadrados encontrados
        cores_ordenadas = ['preto', 'azul', 'verde', 'vermelho', 'branco']
        
        for i, (approx, area) in enumerate(quadrados[:5]):  # Pega os 5 primeiros
            if i >= len(cores_ordenadas):
                break
                
            # Calcula a cor média dentro do quadrado
            mask = np.zeros(img.shape[:2], dtype=np.uint8)
            cv2.fillPoly(mask, [approx], 255)
            
            mean_color = cv2.mean(img, mask=mask)[:3]  # BGR
            mean_rgb = (mean_color[2], mean_color[1], mean_color[0])  # Converte para RGB
            
            nome_cor = cores_ordenadas[i]
            self.cores_detectadas[nome_cor] = mean_rgb
            
            print(f"📊 {nome_cor.capitalize()} detectado: RGB{mean_rgb}")
            
            # Desenha contorno na imagem (opcional)
            cv2.drawContours(img, [approx], 0, (0, 255, 0), 2)
        
        # Salva imagem anotada
        cv2.imwrite("calibracao_detectada.jpg", img)
        print(f"✅ Imagem anotada salva: calibracao_detectada.jpg")
        
        return len(self.cores_detectadas) >= 5
    
    def calcular_correcao(self):
        """
        Calcula a matriz de correção de cores usando regressão linear
        Mapeia as cores detectadas para as cores de referência
        """
        if len(self.cores_detectadas) < 5:
            print("❌ Não há cores detectadas suficientes para calibração")
            return None
        
        # Prepara matrizes para regressão
        X = []  # Cores detectadas (entrada)
        Y = []  # Cores referência (saída esperada)
        
        for nome_cor, cor_detectada in self.cores_detectadas.items():
            if nome_cor in self.cores_referencia:
                X.append(cor_detectada)
                Y.append(self.cores_referencia[nome_cor])
        
        X = np.array(X, dtype=np.float32)
        Y = np.array(Y, dtype=np.float32)
        
        # Calcula matriz de correção (regressão linear)
        # Ajuste de canal por canal (R, G, B independentemente)
        self.matriz_correcao = []
        
        for canal in range(3):  # Para cada canal RGB
            # Ajuste linear: cor_saida = a * cor_entrada + b
            x = X[:, canal]
            y = Y[:, canal]
            
            # Regressão linear simples
            n = len(x)
            a = (n * np.sum(x*y) - np.sum(x)*np.sum(y)) / (n * np.sum(x*x) - np.sum(x)**2)
            b = (np.sum(y) - a * np.sum(x)) / n
            
            self.matriz_correcao.append((a, b))
        
        print("\n✅ Matriz de correção calculada:")
        print(f"   Canal R: corrigir = {self.matriz_correcao[0][0]:.3f} * original + {self.matriz_correcao[0][1]:.1f}")
        print(f"   Canal G: corrigir = {self.matriz_correcao[1][0]:.3f} * original + {self.matriz_correcao[1][1]:.1f}")
        print(f"   Canal B: corrigir = {self.matriz_correcao[2][0]:.3f} * original + {self.matriz_correcao[2][1]:.1f}")
        
        return self.matriz_correcao
    
    def corrigir_cor(self, rgb):
        """Aplica correção a uma única cor"""
        if self.matriz_correcao is None:
            return rgb
        
        r, g, b = rgb
        r_corrigido = max(0, min(255, self.matriz_correcao[0][0] * r + self.matriz_correcao[0][1]))
        g_corrigido = max(0, min(255, self.matriz_correcao[1][0] * g + self.matriz_correcao[1][1]))
        b_corrigido = max(0, min(255, self.matriz_correcao[2][0] * b + self.matriz_correcao[2][1]))
        
        return (int(r_corrigido), int(g_corrigido), int(b_corrigido))
    
    def corrigir_imagem(self, imagem_path, saida_path="imagem_corrigida.jpg"):
        """Aplica correção a uma imagem inteira"""
        if self.matriz_correcao is None:
            print("❌ Calibração não realizada. Execute calibrar() primeiro.")
            return None
        
        img = cv2.imread(imagem_path)
        if img is None:
            print(f"❌ Erro ao carregar: {imagem_path}")
            return None
        
        # Aplica correção pixel a pixel
        img_corrigida = np.zeros_like(img)
        for y in range(img.shape[0]):
            for x in range(img.shape[1]):
                b, g, r = img[y, x]  # OpenCV usa BGR
                r_corrigido, g_corrigido, b_corrigido = self.corrigir_cor((r, g, b))
                img_corrigida[y, x] = (b_corrigido, g_corrigido, r_corrigido)
        
        cv2.imwrite(saida_path, img_corrigida)
        print(f"✅ Imagem corrigida salva: {saida_path}")
        return img_corrigida
    
    def calibrar(self, imagem_referencia_path):
        """Pipeline completo de calibração"""
        print(f"\n🔧 Calibrando com: {imagem_referencia_path}")
        print("-" * 40)
        
        # Detecta quadrados coloridos
        if not self.detectar_quadrados(imagem_referencia_path):
            print("❌ Falha na detecção dos quadrados")
            return False
        
        # Calcula matriz de correção
        self.calcular_correcao()
        
        # Salva calibração para uso futuro
        self.salvar_calibracao("calibracao.json")
        
        return True
    
    def salvar_calibracao(self, arquivo="calibracao.json"):
        """Salva os parâmetros de calibração em arquivo"""
        dados = {
            'cores_detectadas': self.cores_detectadas,
            'matriz_correcao': self.matriz_correcao.tolist() if self.matriz_correcao is not None else None
        }
        
        with open(arquivo, 'w') as f:
            json.dump(dados, f, indent=2)
        
        print(f"✅ Calibração salva: {arquivo}")
    
    def carregar_calibracao(self, arquivo="calibracao.json"):
        """Carrega parâmetros de calibração salvos"""
        if not os.path.exists(arquivo):
            print(f"❌ Arquivo não encontrado: {arquivo}")
            return False
        
        with open(arquivo, 'r') as f:
            dados = json.load(f)
        
        self.cores_detectadas = dados['cores_detectadas']
        # Converte lista para numpy array
        self.matriz_correcao = np.array(dados['matriz_correcao']) if dados['matriz_correcao'] else None
        
        print(f"✅ Calibração carregada: {arquivo}")
        return True

# ========== USO PRÁTICO ==========
def exemplo_calibracao():
    """Exemplo completo de calibração"""
    
    # 1. Cria o cartão de referência (se não existir)
    if not os.path.exists("cartao_calibracao.png"):
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (300, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        cores_pos = [
            ((0, 0, 0), (0, 100, 0, 100)),      # Preto
            ((0, 0, 255), (100, 0, 200, 100)),  # Azul
            ((0, 255, 0), (200, 0, 300, 100)),  # Verde
            ((255, 0, 0), (0, 100, 100, 200)),  # Vermelho
            ((255, 255, 255), (100, 100, 200, 200)), # Branco
        ]
        
        for cor, pos in cores_pos:
            draw.rectangle(pos, fill=cor, outline='black')
        
        img.save("cartao_calibracao.png")
        print("📷 Cartão de calibração criado: cartao_calibracao.png")
    
    # 2. Inicializa calibrador
    calibrador = ColorCalibrator()
    
    # 3. Calibra usando foto do cartão
    # (você precisa tirar uma foto do cartão com sua câmera)
    if os.path.exists("foto_calibracao.jpg"):
        calibrador.calibrar("foto_calibracao.jpg")
    else:
        print("\n⚠️  Para calibrar:")
        print("1. Imprima ou exiba 'cartao_calibracao.png'")
        print("2. Tire uma foto com sua câmera")
        print("3. Salve como 'foto_calibracao.jpg'")
        print("4. Execute novamente")
        return
    
    # 4. Corrige uma foto de teste
    if os.path.exists("foto_teste.jpg"):
        calibrador.corrigir_imagem("foto_teste.jpg", "foto_teste_corrigida.jpg")
    
    # 5. Testa correção de cores isoladas
    print("\n🔮 Teste de correção:")
    cores_teste = [(255,0,0), (0,255,0), (0,0,255), (0,0,0), (255,255,255)]
    for cor in cores_teste:
        cor_corrigida = calibrador.corrigir_cor(cor)
        print(f"  {cor} -> {cor_corrigida}")

def calibrar_com_imagem_web():
    """Calibração usando imagem recebida via web"""
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    calibrador = ColorCalibrator()
    
    @app.route('/calibrar', methods=['POST'])
    def calibrar():
        # Recebe imagem do ESP32-CAM
        file = request.files['image']
        file.save("temp_calibracao.jpg")
        
        # Executa calibração
        sucesso = calibrador.calibrar("temp_calibracao.jpg")
        
        if sucesso:
            # Salva matriz de correção
            calibrador.salvar_calibracao()
            return jsonify({"status": "success", "matriz": calibrador.matriz_correcao.tolist()})
        else:
            return jsonify({"status": "error", "message": "Falha na calibração"})
    
    @app.route('/corrigir', methods=['POST'])
    def corrigir():
        # Corrige imagem recebida
        file = request.files['image']
        file.save("temp_correcao.jpg")
        
        calibrador.carregar_calibracao()
        img_corrigida = calibrador.corrigir_imagem("temp_correcao.jpg")
        
        if img_corrigida is not None:
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error"})
    
    return app

if __name__ == "__main__":
    exemplo_calibracao()