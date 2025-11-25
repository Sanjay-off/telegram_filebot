from pyrogram import Client, filters
from pyrogram.types import Message
import os
from dotenv import load_dotenv
from base64 import urlsafe_b64encode

load_dotenv()

# Telegram credentials
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN_TEMPLATE = os.getenv("BOT_TOKEN_TEMPLATE", "")

# Main bot username (without @) – REQUIRED
MAIN_BOT_USERNAME = os.getenv("BOT_USERNAME", "YourMainBotUsername")


# ------------------------------------------------------------
# FONT HELPERS
# ------------------------------------------------------------

def italic(text: str) -> str:
    base = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    italic_chars = (
        "𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡"
        "𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻"
    )
    table = str.maketrans({base[i]: italic_chars[i] for i in range(len(base))})
    return text.translate(table)


def fancy_title(text: str) -> str:
    mapping = str.maketrans({
        "A": "🅰", "B": "🅱", "C": "🅲", "D": "🅳",
        "E": "🅴", "F": "🅵", "G": "🅶", "H": "🅷",
        "I": "🅸", "J": "🅹", "K": "🅺", "L": "🅻",
        "M": "🅼", "N": "🅽", "O": "🅾", "P": "🅿",
        "Q": "🆀", "R": "🆁", "S": "🆂", "T": "🆃",
        "U": "🆄", "V": "🆅", "W": "🆆", "X": "🆇",
        "Y": "🆈", "Z": "🆉",
    })
    return text.upper().translate(mapping)


# ------------------------------------------------------------
# HELPER → Encode deep-link file code
# ------------------------------------------------------------

def encode_file_code(raw: str) -> str:
    return urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")


# ------------------------------------------------------------
# STATE MEMORY (one-time inline data)
# ------------------------------------------------------------
STATE = {}   # { user_id: { file_msg, post_number, description } }


# ------------------------------------------------------------
# TEMPLATE BOT CLIENT
# ------------------------------------------------------------
app = Client(
    "template_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN_TEMPLATE
)


# ------------------------------------------------------------
# COMMAND: /start
# ------------------------------------------------------------
@app.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    await message.reply_text(
        "Send me a ZIP/VIDEO/FILE.\n\n"
        "Then I will ask:\n"
        "1️⃣ Post number\n"
        "2️⃣ Description\n\n"
        "And generate your **public group template** automatically."
    )


# ------------------------------------------------------------
# MAIN HANDLER: File → Post number → Description → Template
# ------------------------------------------------------------
@app.on_message(filters.private & ~filters.command(["start"]))
async def template_flow(client: Client, message: Message):
    user_id = message.from_user.id

    # Load previous state if exists
    state = STATE.get(user_id)

    # Step 1 — Expect FILE
    if not state:
        if not (message.document or message.video or message.audio):
            await message.reply_text("❌ Please send a **file** first.")
            return

        # Store the file message
        STATE[user_id] = {"file_msg": message}
        await message.reply_text("ᵀʸᵖᵉ ᵖᵒˢᵗ ⁿᵘᵐᵇᵉʳ (Example: 23):")
        return

    # Step 2 — Expect POST NUMBER
    if "post_number" not in state:
        post_number = message.text.strip()

        if not post_number.isdigit():
            await message.reply_text("❌ Post number must be digits only.\nTry again:")
            return

        state["post_number"] = post_number
        STATE[user_id] = state

        await message.reply_text("𝘕𝘰𝘸 𝘵𝘺𝘱𝘦 𝘵𝘩𝘦 𝘥𝘦𝘴𝘤𝘳𝘪𝘱𝘵𝘪𝘰𝘯:")
        return

    # Step 3 — Expect DESCRIPTION
    if "description" not in state:
        description = message.text.strip()
        state["description"] = description
        STATE[user_id] = state

        # Now generate template
        await generate_template(client, message, state)

        # Clear state
        STATE.pop(user_id, None)
        return


# ------------------------------------------------------------
# TEMPLATE GENERATOR
# ------------------------------------------------------------
async def generate_template(client: Client, message: Message, st: dict):
    post_number = st["post_number"]
    desc = st["description"]

    # Build encoded deep-link
    raw_code = f"file_{post_number}"
    encoded = encode_file_code(raw_code)

    # Build header
    header = fancy_title(f"Post - {post_number}")

    # Build final message
    lines = [
        f"**{header}**",
        "",
        f"𝘋𝘦𝘴𝘤𝘳𝘪𝘱𝘵𝘪𝘰𝘯: {italic(desc)}",
        "",
        "⬇ **𝗗𝗢𝗪𝗡𝗟𝗢𝗔𝗗** ⬇",
        "",
        f"[DOWNLOAD](https://t.me/{MAIN_BOT_USERNAME}?start={encoded})"
    ]

    await message.reply_text("\n".join(lines), disable_web_page_preview=True)
