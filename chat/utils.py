from io import BytesIO

from PIL import Image


def binary_to_webp(binary):
    image = Image.open(BytesIO(binary))

    # Convert image to WebP format
    output = BytesIO()
    image.save(output, "WEBP")
    output.seek(0)

    return output
