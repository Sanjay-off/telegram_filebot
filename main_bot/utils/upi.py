import io
import qrcode
from ..config import UPI_ID


# ------------------------------------------------------------
# Build UPI payment URI
# ------------------------------------------------------------

def build_upi_uri(amount: int, order_id: str) -> str:
    """
    Create a UPI payment URI using your hidden UPI ID.
    This URI is embedded inside the QR code.

    Pattern:
    upi://pay?pa=<upi_id>&am=<amount>&tn=<order_id>&cu=INR
    """
    return f"upi://pay?pa={UPI_ID}&am={amount}&tn={order_id}&cu=INR"


# ------------------------------------------------------------
# Generate a QR code PNG for UPI
# ------------------------------------------------------------

def generate_qr_png(upi_uri: str):
    """
    Create a PNG QR code for the UPI payment URI.
    Returns a BytesIO object that Pyrogram can send directly.

    Example:
        qr_buf = generate_qr_png(upi_uri)
        await message.reply_photo(photo=qr_buf)
    """
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=2,
    )
    qr.add_data(upi_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)  # move pointer back to start

    return buf
