#!/usr/bin/env python3
"""
Cria uma imagem de referência para calibração de cores
Padrão: 2x3 quadrados: Preto, Azul, Verde, Vermelho, Branco
"""

from PIL import Image, ImageDraw

def criar_cartao_calibracao(tamanho_quadrado=100, arquivo_saida="cartao_calibracao.png"):
    """Cria cartão de calibração com quadrados coloridos"""
    
    # Dimensões: 3 colunas x 2 linhas
    largura = tamanho_quadrado * 3
    altura = tamanho_quadrado * 2
    img = Image.new('RGB', (largura, altura), color='white')
    draw = ImageDraw.Draw(img)
    
    # Cores: (nome, RGB, posição coluna, posição linha)
    cores = [
        ("Preto", (0, 0, 0), 0, 0),
        ("Azul", (0, 0, 255), 1, 0),
        ("Verde", (0, 255, 0), 2, 0),
        ("Vermelho", (255, 0, 0), 0, 1),
        ("Branco", (255, 255, 255), 1, 1),
        ("Cinza", (128, 128, 128), 2, 1),  # Opcional: cinza médio
    ]
    
    # Desenha os quadrados
    for nome, cor_rgb, col, linha in cores:
        x1 = col * tamanho_quadrado
        y1 = linha * tamanho_quadrado
        x2 = x1 + tamanho_quadrado
        y2 = y1 + tamanho_quadrado
        
        draw.rectangle([x1, y1, x2, y2], fill=cor_rgb, outline='black', width=2)
        
        # Adiciona texto (opcional)
        # draw.text((x1+5, y1+5), nome[:1], fill='white' if col<2 else 'black')
    
    img.save(arquivo_saida)
    print(f"✅ Cartão de calibração salvo: {arquivo_saida}")
    print(f"   Dimensões: {largura}x{altura}")
    return arquivo_saida

if __name__ == "__main__":
    criar_cartao_calibracao(tamanho_quadrado=100)