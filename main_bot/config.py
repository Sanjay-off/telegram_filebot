import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# ----------------------------------------------------
# Telegram API Credentials
# ----------------------------------------------------
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")

# Main bot token (delivery + verification + premium)
BOT_TOKEN_MAIN = os.getenv("BOT_TOKEN_MAIN", "")

# ----------------------------------------------------
# MongoDB
# ----------------------------------------------------
MONGO_URL = os.getenv("MONGO_URL", "")

# ----------------------------------------------------
# Admins (list of ints)
# ----------------------------------------------------
ADMIN_IDS = set()
_admin_raw = os.getenv("ADMIN_IDS", "")
if _admin_raw:
    for x in _admin_raw.split(","):
        x = x.strip()
        if x.isdigit():
            ADMIN_IDS.add(int(x))

# ----------------------------------------------------
# Storage channel (private)
# Example: -1001234567890
# ----------------------------------------------------
STORAGE_CHANNEL_ID = int(os.getenv("STORAGE_CHANNEL_ID", "0"))

# ----------------------------------------------------
# Force Subscribe Channels (optional)
# Comma-separated list of channel IDs
# ----------------------------------------------------
FORCE_SUB_CHANNELS = []
_force = os.getenv("FORCE_SUB_CHANNELS", "")
if _force:
    for ch in _force.split(","):
        ch = ch.strip()
        if ch.startswith("-100") and ch[4:].isdigit():
            FORCE_SUB_CHANNELS.append(int(ch))

# ----------------------------------------------------
# Optional logging channel
# ----------------------------------------------------
LOG_CHANNEL_ID = None
_log = os.getenv("LOG_CHANNEL_ID", "").strip()
if _log.startswith("-100") and _log[4:].isdigit():
    LOG_CHANNEL_ID = int(_log)

# ----------------------------------------------------
# Bot Usernames (without @)
# ----------------------------------------------------
BOT_USERNAME = os.getenv("BOT_USERNAME", "")
TEMPLATE_BOT_USERNAME = os.getenv("TEMPLATE_BOT_USERNAME", "")

# ----------------------------------------------------
# Payment (UPI)
# ----------------------------------------------------
# UPI ID is **never shown to the user**
# Only encoded inside the QR generated for payments.
UPI_ID = os.getenv("UPI_ID", "")

# ----------------------------------------------------
# Shortener API (optional)
# ----------------------------------------------------
SHORTENER_API_KEY = os.getenv("SHORTENER_API_KEY", "")
SHORTENER_BASE_URL = os.getenv("SHORTENER_BASE_URL", "")
