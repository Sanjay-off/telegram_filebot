import base64
from .fonts import fancy_title

def b64_encode(text: str) -> str:
    """
    Encode a string to URL-safe Base64.
    Used for deep-links (file codes, verification tokens, etc).
    """
    return base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii")


def b64_decode(text: str) -> str:
    """
    Decode a URL-safe Base64 string back to normal text.
    Returns empty string on any error.
    """
    try:
        return base64.urlsafe_b64decode(text.encode("ascii")).decode("utf-8")
    except Exception:
        return ""


def build_file_caption(password: str, delete_minutes: int) -> str:
    """
    Build the caption shown under the delivered ZIP file.

    - Uses fancy title style
    - Shows only the password value in code block (easy to copy)
    - Adds auto-delete info if delete_minutes > 0
    """
    title = fancy_title("File Ready ✔")
    lines = []
    lines.append(f"**{title}**")
    lines.append("")
    lines.append("**🗝️ Password**")
    lines.append(f"`{password}`")  # only the value is copyable, not the word "password"
    lines.append("")
    if delete_minutes > 0:
        lines.append(
            f"ᵀʰⁱˢ ᶠⁱˡᵉ ʷⁱˡˡ ᵇᵉ ᵃᵘᵗᵒ-ᵈᵉˡᵉᵗᵉᵈ ⁱⁿ {delete_minutes} ᵐⁱⁿᵘᵗᵉˢ."
        )
    return "\n".join(lines)
