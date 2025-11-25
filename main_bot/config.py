import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN_MAIN = os.getenv("BOT_TOKEN_MAIN", "")

MONGO_URL = os.getenv("MONGO_URL", "")

# Admins
ADMIN_IDS = set()
_admins = os.getenv("ADMIN_IDS", "")
if _admins:
    for part in _admins.split(","):
        part = part.strip()
        if part.isdigit():
            ADMIN_IDS.add(int(part))

# Storage channel (for your ZIP files)
STORAGE_CHANNEL_ID = int(os.getenv("STORAGE_CHANNEL_ID", "0"))

# Optional: force-subscribe channels (channel IDs)
FORCE_SUB_CHANNELS = []
_force = os.getenv("FORCE_SUB_CHANNELS", "")
if _force:
    for part in _force.split(","):
        part = part.strip()
        if part.startswith("-100") and part[4:].isdigit():
            FORCE_SUB_CHANNELS.append(int(part))

# Optional log channel
LOG_CHANNEL_ID = None
_log_ch = os.getenv("LOG_CHANNEL_ID", "").strip()
if _log_ch.startswith("-100") and _log_ch[4:].isdigit():
    LOG_CHANNEL_ID = int(_log_ch)

# UPI / Shortener (plug real APIs if you want)
UPI_ID = os.getenv("UPI_ID", "")
SHORTENER_API_KEY = os.getenv("SHORTENER_API_KEY", "")
SHORTENER_BASE_URL = os.getenv("SHORTENER_BASE_URL", "")

# Bot usernames
BOT_USERNAME = os.getenv("BOT_USERNAME", "")
TEMPLATE_BOT_USERNAME = os.getenv("TEMPLATE_BOT_USERNAME", "")
