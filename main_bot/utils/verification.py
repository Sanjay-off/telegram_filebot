from .common import b64_encode, b64_decode

# ------------------------------------------------------------
# Generate a verification token for the user
# ------------------------------------------------------------

def generate_verification_token(user_id: int) -> str:
    """
    Create a unique verification token for the user.
    Pattern used: verify_<user_id>
    """
    return f"verify_{user_id}"


# ------------------------------------------------------------
# Base64 encode/decode helpers (just wrappers)
# ------------------------------------------------------------

def encode_verification_token(token: str) -> str:
    return b64_encode(token)


def decode_verification_token(encoded: str) -> str:
    return b64_decode(encoded)


# ------------------------------------------------------------
# Anti-bypass check (placeholder)
# ------------------------------------------------------------

def check_shortener_verification(user_id: int, token: str) -> bool:
    """
    The real logic should verify that:
    - The user actually visited all required shortener pages
    - The request came from your shortener callback or log API
    - The flow wasn't bypassed by 3rd-party bypass sites

    CURRENT BEHAVIOR:
    ALWAYS returns True so your bot works normally.

    Replace this with real verification later.
    """
    return True
