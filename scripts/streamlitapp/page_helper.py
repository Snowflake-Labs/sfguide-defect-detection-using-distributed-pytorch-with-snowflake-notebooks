import base64, io
from PIL import Image


def get_image(image_name):
    pil_im = Image.open(image_name)
    b = io.BytesIO()
    pil_im.save(b, 'png')
    img_bytes = b.getvalue()
    
    content = base64.b64encode(img_bytes).decode()
    img = f"data:image/png;base64,{content}"

    return img