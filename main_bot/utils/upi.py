import io
import qrcode
from ..config import UPI_ID

def build_upi_uri(amount: int, order_id: str) -> str:
    # UPI ID never shown to user directly, only inside QR
    return f"upi://pay?pa={UPI_ID}&am={amount}&tn={order_id}&cu=INR"

def generate_qr_png(upi_uri: str) -> bytes:
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(upi_uri)
    qr.make(fit=True)
    img = qr.make_image()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()
