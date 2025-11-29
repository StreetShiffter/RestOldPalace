import qrcode
from io import BytesIO
from base64 import b64encode
from django import template

register = template.Library()


@register.simple_tag
def qr_from_text(text, size=200):
    """Отдельный генератор QR кода на оплату в шаблоне"""
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_str = b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"
