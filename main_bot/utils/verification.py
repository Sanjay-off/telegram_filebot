from .common import b64_encode, b64_decode

# This file is where you'd integrate real shortener anti-bypass logic.

def generate_verification_token(user_id: int) -> str:
    # Eg: "verify:<user_id>:<random>"
    raw = f"verify_{user_id}"
    return raw

def encode_verification_token(token: str) -> str:
    return b64_encode(token)

def decode_verification_token(encoded: str) -> str:
    return b64_decode(encoded)

def check_shortener_verification(user_id: int, token: str) -> bool:
    """
    TODO: Integrate with your URL shortener API here.
    For now, we simply return True so flow works.
    """
    return True
