from PIL import Image

# Abrir imagem
img = Image.open("/bats/fotos/ramdisk/entrada.jpg").convert("RGB")

# Obter dimensões
width, height = img.size

# Criar imagem de saída
out = Image.new("RGB", (width, height))
contador=0

for y in range(height):
    for x in range(width):

        r, g, b = img.getpixel((x, y))

        verde_dominante = (
            g > r * 1.1 and
            g > b * 1.1 and
            g > 30 and
            r < 200
        )

        if verde_dominante:
           contador += 1
        else:
           contador=0

        if verde_dominante and contador >10:
            out.putpixel((x, y), (r, g, b))
            out.putpixel((x, y), (r,int(g*3), b))
        else:
           if r<20 and g<20 and b<20:
              out.putpixel((x, y), (0, 0, 0))
           else:
             gray = int((r + g + b) / 3)
#             out.putpixel((x, y), (gray, gray, gray))
             out.putpixel((x, y), (255, 255, 255))

out.save("/bats/fotos/ramdisk/saida.jpg")

print("Imagem processada.")