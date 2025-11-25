import asyncio
from datetime import datetime, timedelta

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InputMediaPhoto

from config import API_ID, API_HASH, BOT_TOKEN_MAIN, ADMIN_IDS
from utils.fonts import italic
from utils.common import b64_decode, build_file_caption
from utils.keyboards import (
    main_menu_kb,
    verification_kb,
    deleted_message_kb,
    premium_menu_kb,
)
from utils.verification import (
    generate_verification_token,
    decode_verification_token,
    check_shortener_verification,
)
from utils.upi import build_upi_uri, generate_qr_png
from db import (
    get_user,
    update_user,
    get_settings,
    set_setting,
    count_users,
    create_payment,
    mark_payment_paid,
)

app = Client("main_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN_MAIN)

# TODO: replace this with real file_id from your storage channel
TEST_FILE_ID = "PUT_YOUR_FILE_ID_HERE"

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def send_wait(msg: Message) -> Message:
    return await msg.reply_text("⏳ " + italic("Please wait…"))

# ───────────────────────── COMMANDS ─────────────────────────

@app.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    get_user(user_id)  # ensure exist

    parts = message.text.split(maxsplit=1)
    deep = parts[1].strip() if len(parts) > 1 else ""

    if deep:
        decoded = b64_decode(deep)
        # file deep-link: b64("file_<code>")
        if decoded.startswith("file_"):
            file_code = decoded.split("_", 1)[1]
            wait = await send_wait(message)
            await handle_file_request(client, message, wait, file_code)
            return
        # verification deep-link (optional)
        if decoded.startswith("verify_"):
            wait = await send_wait(message)
            token = decoded
            if check_shortener_verification(user_id, token):
                settings = get_settings()
                update_user(
                    user_id,
                    {
                        "is_verified": True,
                        "verified_until": datetime.utcnow()
                        + timedelta(days=settings["verification_days"]),
                        "downloads_left": settings["free_downloads"],
                    },
                )
                await wait.edit_text("✅ Verification successful! You can now download files.")
            else:
                await wait.edit_text("❌ Bypass detected. Please use the original verification link.")
            return

    text = (
        "👋 Welcome!\n\n"
        "Use the buttons or /help to learn how to use this bot."
    )
    await message.reply_text(text, reply_markup=main_menu_kb())

@app.on_message(filters.command("help"))
async def help_cmd(client: Client, message: Message):
    text = (
        "**How to use this bot:**\n\n"
        "1. Open the public group and tap the DOWNLOAD button.\n"
        "2. If needed, complete verification.\n"
        "3. After verification, start this bot via the deep link.\n"
        "4. Premium users (via UPI) can skip verification & limits."
    )
    await message.reply_text(text)

@app.on_message(filters.command("premium_status"))
async def premium_status_cmd(client: Client, message: Message):
    user = get_user(message.from_user.id)
    if user.get("is_premium") and user.get("premium_until"):
        await message.reply_text(
            "💎 PREMIUM STATUS\n\n"
            f"Status: **ACTIVE**\n"
            f"Expires: `{user['premium_until']}`"
        )
    else:
        await message.reply_text(
            "👤 PREMIUM STATUS\n\n"
            "Status: **NOT PREMIUM**\n"
            "You can continue as a free user."
        )

# ───────────────────────── FILE REQUEST ─────────────────────────

async def handle_file_request(client: Client, message: Message, wait_msg: Message, file_code: str):
    user = get_user(message.from_user.id)
    settings = get_settings()

    now = datetime.utcnow()
    # Premium override
    if not user.get("is_premium") or not user.get("premium_until") or user["premium_until"] < now:
        # require verification
        if not user.get("is_verified") or not user.get("verified_until") or user["verified_until"] < now:
            # show verification template
            token = generate_verification_token(message.from_user.id)
            kb = verification_kb(token, settings["verify_link"])
            await wait_msg.edit_text(
                "🔐 You must verify before downloading.\nTap VERIFY NOW or watch the guide.",
                reply_markup=kb,
            )
            return
        # check download limit
        if user.get("downloads_left", 0) <= 0:
            token = generate_verification_token(message.from_user.id)
            kb = verification_kb(token, settings["verify_link"])
            await wait_msg.edit_text(
                "⚠ You've reached your free download limit.\nPlease verify again.",
                reply_markup=kb,
            )
            return
        # decrement downloads_left
        update_user(user["_id"], {"downloads_left": user.get("downloads_left", 0) - 1})

    # send file
    caption = build_file_caption(settings["zip_password"], settings["delete_time_minutes"])
    try:
        sent = await client.send_document(
            chat_id=message.chat.id,
            document=TEST_FILE_ID,
            caption=caption,
        )
        await wait_msg.delete()
        # schedule auto-delete
        if settings["delete_time_minutes"] > 0:
            asyncio.create_task(
                delete_file_later(client, sent.chat.id, sent.id, settings["delete_time_minutes"], file_code)
            )
    except Exception as e:
        await wait_msg.edit_text(
            f"❌ Failed to send file. Configure TEST_FILE_ID.\n`{e}`"
        )

async def delete_file_later(client: Client, chat_id: int, msg_id: int, minutes: int, file_code: str):
    await asyncio.sleep(minutes * 60)
    try:
        await client.delete_messages(chat_id, msg_id)
    except Exception:
        pass
    await client.send_message(
        chat_id=chat_id,
        text=(
            "🗑 𝘗𝘳𝘦𝘷𝘪𝘰𝘶𝘴 𝘮𝘦𝘴𝘴𝘢𝘨𝘦 𝘸𝘢𝘴 𝘥𝘦𝘭𝘦𝘵𝘦𝘥.\n"
            "𝘜𝘴𝘦 𝘵𝘩𝘦 𝘣𝘶𝘵𝘵𝘰𝘯 𝘣𝘦𝘭𝘰𝘸 𝘵𝘰 𝘨𝘦𝘵 𝘪𝘵 𝘢𝘨𝘢𝘪𝘯."
        ),
        reply_markup=deleted_message_kb(file_code),
    )

# ───────────────────────── CALLBACKS ─────────────────────────

@app.on_callback_query()
async def callbacks(client: Client, cq: CallbackQuery):
    data = cq.data or ""
    user_id = cq.from_user.id

    # Refile (after deletion)
    if data.startswith("refile:"):
        encoded = data.split(":", 1)[1]
        decoded = b64_decode(encoded)
        if decoded.startswith("file_"):
            file_code = decoded.split("_", 1)[1]
            wait = await cq.message.reply_text("⏳ " + italic("Please wait…"))
            await handle_file_request(client, cq.message, wait, file_code)
        await cq.answer()
        return

    if data == "close_msg":
        try:
            await cq.message.delete()
        except Exception:
            pass
        await cq.answer()
        return

    # From verification keyboard
    if data.startswith("verify:"):
        encoded = data.split(":", 1)[1]
        token = decode_verification_token(encoded)
        # Anti-bypass hook
        if check_shortener_verification(user_id, token):
            settings = get_settings()
            update_user(
                user_id,
                {
                    "is_verified": True,
                    "verified_until": datetime.utcnow()
                    + timedelta(days=settings["verification_days"]),
                    "downloads_left": settings["free_downloads"],
                },
            )
            await cq.message.edit_text(
                "✅ Verification successful!\nYou can now go back to the post and tap DOWNLOAD again."
            )
        else:
            await cq.message.edit_text(
                "❌ Bypass detected.\nPlease open the real shortener link and try again."
            )
        await cq.answer()
        return

    # Main menu callbacks
    if data == "menu_get_file":
        await cq.answer("Use the DOWNLOAD button in public posts to request files.", show_alert=True)
        return

    if data == "menu_help":
        await cq.answer("Use /help to learn how to use this bot.", show_alert=True)
        return

    if data == "menu_premium":
        # Show simple UPI QR skeleton
        settings = get_settings()
        amount = 50  # example amount
        order_id = create_payment(user_id, "Premium", amount)
        upi_uri = build_upi_uri(amount, order_id)
        qr_png = generate_qr_png(upi_uri)
        await cq.message.reply_photo(
            photo=qr_png,
            caption=(
                "💎 Premium Payment (Skeleton)\n\n"
                f"Order ID: `{order_id}`\n"
                f"Plan: Premium\n"
                "Pay using this QR within 10 minutes.\n"
                "Then tap 'I've Paid, Verify Payment'.\n\n"
                "_Note: Real auto-verification requires UPI API integration._"
            ),
            reply_markup=premium_menu_kb(order_id),
        )
        await cq.answer()
        return

    if data.startswith("pay_verify:"):
        order_id = data.split(":", 1)[1]
        # Here you would call your UPI API / check bank logs.
        # For now we simulate success.
        settings = get_settings()
        prem_minutes = settings["premium_minutes"]
        premium_until = mark_payment_paid(order_id, prem_minutes)
        if premium_until:
            await cq.message.edit_caption(
                caption=(
                    f"✅ Payment verified!\nPremium active until: `{premium_until}`\n"
                    "You can now download files without limits."
                ),
                reply_markup=premium_menu_kb(),
            )
        else:
            await cq.answer("Payment not found or already processed.", show_alert=True)
        return

# ───────────────────────── ADMIN COMMANDS ─────────────────────────

@app.on_message(filters.command("admin"))
async def admin_cmd(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply_animation(
            animation="https://media.giphy.com/media/3og0IPxMM0erATueVW/giphy.gif",
            caption="💀 ACCESS DENIED 💀\nAdmins only.",
        )
        return
    text = (
        "🛠 **Admin Panel**\n\n"
        "/stats - Show user stats\n"
        "/settings - Show current settings\n"
        "/set <key> <value> - Update setting\n\n"
        "Supported keys:\n"
        "- verify_link (URL string)\n"
        "- delete_time_minutes (int)\n"
        "- verification_days (int)\n"
        "- free_downloads (int)\n"
        "- zip_password (string)\n"
        "- premium_minutes (int)\n"
    )
    await message.reply_text(text)

@app.on_message(filters.command("stats"))
async def stats_cmd(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply_text("🚫 Admins only.")
        return
    wait = await send_wait(message)
    total, verified, premium = count_users()
    await wait.edit_text(
        "📊 **Bot Stats**\n\n"
        f"Total users: `{total}`\n"
        f"Verified users: `{verified}`\n"
        f"Premium users: `{premium}`"
    )

@app.on_message(filters.command("settings"))
async def settings_cmd(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply_text("🚫 Admins only.")
        return
    s = get_settings()
    text = (
        "⚙ **Current Settings**\n\n"
        f"verify_link: `{s['verify_link']}`\n"
        f"delete_time_minutes: `{s['delete_time_minutes']}`\n"
        f"verification_days: `{s['verification_days']}`\n"
        f"free_downloads: `{s['free_downloads']}`\n"
        f"zip_password: `{s['zip_password']}`\n"
        f"premium_minutes: `{s['premium_minutes']}`"
    )
    await message.reply_text(text)

@app.on_message(filters.command("set"))
async def set_cmd(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply_text("🚫 Admins only.")
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.reply_text("Usage: /set <key> <value>")
        return
    key = parts[1].strip()
    raw_val = parts[2].strip()
    int_keys = ["delete_time_minutes", "verification_days", "free_downloads", "premium_minutes"]
    str_keys = ["verify_link", "zip_password"]

    if key not in int_keys + str_keys:
        await message.reply_text("❌ Unsupported key.")
        return

    if key in int_keys:
        try:
            val = int(raw_val)
        except ValueError:
            await message.reply_text("❌ Value must be an integer.")
            return
    else:
        val = raw_val

    set_setting(key, val)
    await message.reply_text(f"✅ `{key}` updated to `{val}`")

if __name__ == "__main__":
    app.run()
