import base64
from .fonts import fancy_title

def b64_encode(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii")

def b64_decode(text: str) -> str:
    try:
        return base64.urlsafe_b64decode(text.encode("ascii")).decode("utf-8")
    except Exception:
        return ""

def build_file_caption(password: str, delete_minutes: int) -> str:
    title = fancy_title("File Ready ✔")
    lines = []
    lines.append(f"**{title}**")
    lines.append("")
    lines.append("**🗝️ Password**")
    lines.append(f"`{password}`")  # only value is copyable
    lines.append("")
    if delete_minutes > 0:
        lines.append(f"ᵀʰⁱˢ ᶠⁱˡᵉ ʷⁱˡˡ ᵇᵉ ᵃᵘᵗᵒ-ᵈᵉˡᵉᵗᵉᵈ ⁱⁿ {delete_minutes} ᵐⁱⁿᵘᵗᵉˢ.")
    return "\n".join(lines)
