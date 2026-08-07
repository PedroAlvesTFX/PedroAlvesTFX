#!/usr/bin/env python3
"""
Versão ultra-rápida - apenas com PIL (sem numpy/opencv)
"""

from PIL import Image
import sys
import os
import time

# Cores aproximadas
def cor_para_caractere(r, g, b):
    # Branco
    if r > 200 and g > 200 and b > 200:
        return 'W'
    # Preto
    if r < 50 and g < 50 and b < 50:
        return 'P'
    # Vermelho (predomina vermelho)
    if r > g + 30 and r > b + 30:
        return 'R'
    # Verde (predomina verde)
    if g > r + 30 and g > b + 30:
        return 'G'
    # Azul (predomina azul)
    if b > r + 30 and b > g + 30:
        return 'B'
    # Padrão: preto
    return 'P'

def converter_rapido(caminho_imagem, largura=32, altura=18):
    """Conversão rápida sem numpy"""
    img = Image.open(caminho_imagem)
    img = img.resize((largura, altura), Image.Resampling.LANCZOS)
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    pixels = img.load()
    
    matriz = []
    for y in range(altura):
        linha = []
        for x in range(largura):
            r, g, b = pixels[x, y]
            linha.append(cor_para_caractere(r, g, b))
        matriz.append(''.join(linha))
    
    return matriz

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 ascii_rapido.py <imagem>")
        sys.exit(1)
    
    inicio = time.time()
    matriz = converter_rapido(sys.argv[1], 32, 18)
    fim = time.time()
    
    print(f"\n⏱️  Processado em {(fim-inicio)*1000:.0f} ms\n")
    print("="*32)
    for linha in matriz:
        print(linha)
    print("="*32)