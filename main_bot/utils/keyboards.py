from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .common import b64_encode

def main_menu_kb():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📥 Get File", callback_data="menu_get_file")],
            [InlineKeyboardButton("💎 Premium", callback_data="menu_premium")],
            [InlineKeyboardButton("❓ Help", callback_data="menu_help")],
        ]
    )

def verification_kb(verify_token: str, how_to_verify_url: str | None = None):
    encoded = b64_encode(verify_token)
    buttons = [
        [InlineKeyboardButton("✅ VERIFY NOW", callback_data=f"verify:{encoded}")],
    ]
    if how_to_verify_url:
        buttons.append([InlineKeyboardButton("📺 How to Verify", url=how_to_verify_url)])
    return InlineKeyboardMarkup(buttons)

def deleted_message_kb(file_code: str):
    encoded = b64_encode(f"file_{file_code}")
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("♻ Click Here", callback_data=f"refile:{encoded}")],
            [InlineKeyboardButton("✖ Close", callback_data="close_msg")],
        ]
    )

def premium_menu_kb(order_id: str | None = None):
    rows = []
    if order_id:
        rows.append([InlineKeyboardButton("✅ I've Paid, Verify Payment", callback_data=f"pay_verify:{order_id}")])
    rows.append([InlineKeyboardButton("✖ Close", callback_data="close_msg")])
    return InlineKeyboardMarkup(rows)
