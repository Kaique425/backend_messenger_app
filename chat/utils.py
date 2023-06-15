from io import BytesIO

from PIL import Image


def binary_to_webp(binary):
    image = Image.open(BytesIO(binary))

    # Converter a imagem para o formato WebP
    output = BytesIO()
    image.save(output, "WEBP")
    output.seek(0)

    return output
