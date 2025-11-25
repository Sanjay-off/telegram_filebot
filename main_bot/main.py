import asyncio
from datetime import datetime, timedelta

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from .config import (
    API_ID,
    API_HASH,
    BOT_TOKEN_MAIN,
    ADMIN_IDS,
    FORCE_SUB_CHANNELS,
)
from .utils.fonts import italic
from .utils.common import b64_decode, build_file_caption, b64_encode
from .utils.keyboards import (
    main_menu_kb,
    verification_kb,
    deleted_message_kb,
    premium_menu_kb,
)
from .utils.verification import (
    generate_verification_token,
    decode_verification_token,
    check_shortener_verification,
)
from .utils.upi import build_upi_uri, generate_qr_png
from .db import (
    get_user,
    update_user,
    get_settings,
    set_setting,
    count_users,
    create_payment,
    mark_payment_paid,
)

# Pyrogram client
app = Client("main_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN_MAIN)

# TODO: Replace this with real file_id from your storage channel
TEST_FILE_ID = "PUT_YOUR_FILE_ID_HERE"


# ───────────────────────── Helpers ─────────────────────────

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def send_wait(msg: Message) -> Message:
    """
    Send a 'please wait' message that will be replaced later.
    """
    return await msg.reply_text("⏳ " + italic("Please wait…"))


async def check_and_handle_force_sub(
    client: Client,
    user_id: int,
    wait_msg: Message,
    file_code: str,
) -> bool:
    """
    Check if user has joined all FORCE_SUB_CHANNELS.
    If not, edit wait_msg with a "join all channels & try again" message + button.
    Returns True if OK (user is subscribed or no force-sub), False otherwise.
    """
    if not FORCE_SUB_CHANNELS:
        return True  # no force-sub configured

    missing_channels = []
    channel_titles = {}

    for ch_id in FORCE_SUB_CHANNELS:
        try:
            member = await client.get_chat_member(ch_id, user_id)
            if member.status in ("left", "kicked", "banned"):
                missing_channels.append(ch_id)
        except Exception:
            # If we can't fetch membership, treat as not subscribed
            missing_channels.append(ch_id)

    if not missing_channels:
        return True

    # Try to get channel titles
    for ch_id in missing_channels:
        try:
            chat = await client.get_chat(ch_id)
            channel_titles[ch_id] = chat.title or str(ch_id)
        except Exception:
            channel_titles[ch_id] = str(ch_id)

    lines = [
        "🔒 ᶠᵒʳᶜᵉ ˢᵘᵇˢᶜʳⁱᵖᵗⁱᵒⁿ ʳᵉᵠᵘⁱʳᵉᵈ",
        "",
        "You must join all required channels before you can download files:",
        "",
    ]
    for ch_id in missing_channels:
        lines.append(f"• {channel_titles[ch_id]}")

    lines.append("")
    lines.append("After joining, tap **Try Again** below.")

    # Encode file_code so we can retry the exact same file
    encoded_file = b64_encode(f"file_{file_code}")
    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔁 Try Again", callback_data=f"retry_file:{encoded_file}")]]
    )

    await wait_msg.edit_text("\n".join(lines), reply_markup=kb)
    return False


# ───────────────────────── Commands ─────────────────────────


@app.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    get_user(user_id)  # ensure user exists in DB

    parts = message.text.split(maxsplit=1)
    deep = parts[1].strip() if len(parts) > 1 else ""

    # Deep-link handling
    if deep:
        decoded = b64_decode(deep)

        # File deep-link: b64("file_<code>")
        if decoded.startswith("file_"):
            file_code = decoded.split("_", 1)[1]
            wait = await send_wait(message)
            await handle_file_request(client, message, wait, file_code)
            return

        # Verification deep-link: b64("verify_<id>")
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
                await wait.edit_text(
                    "✅ Verification successful! You can now download files."
                )
            else:
                await wait.edit_text(
                    "❌ Bypass detected. Please use the original verification link."
                )
            return

    # Normal /start
    text = (
        "👋 Welcome!\n\n"
        "Use the buttons or /help to learn how to use this bot."
    )
    await message.reply_text(text, reply_markup=main_menu_kb())


@app.on_message(filters.command("help"))
async def help_cmd(client: Client, message: Message):
    text = (
        "**How to use this bot:**\n\n"
        "1. Go to the public group and tap the **DOWNLOAD** button on a post.\n"
        "2. If asked, complete verification (shortener + channels).\n"
        "3. After verification, tap DOWNLOAD again and you’ll get the file here.\n"
        "4. Premium users can skip verification & limits.\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/premium_status - Check your premium status\n"
    )
    await message.reply_text(text)


@app.on_message(filters.command("premium_status"))
async def premium_status_cmd(client: Client, message: Message):
    user = get_user(message.from_user.id)
    if user.get("is_premium") and user.get("premium_until"):
        await message.reply_text(
            "💎 PREMIUM STATUS\n\n"
            "Status: **ACTIVE**\n"
            f"Expires: `{user['premium_until']}`"
        )
    else:
        await message.reply_text(
            "👤 PREMIUM STATUS\n\n"
            "Status: **NOT PREMIUM**\n"
            "You are currently a free user."
        )


# ───────────────────────── File Handling ─────────────────────────


async def handle_file_request(
    client: Client,
    message: Message,
    wait_msg: Message,
    file_code: str,
):
    """
    Handles file delivery flow:
    - Force-sub check
    - Verification check
    - Free download limit
    - Premium override
    - Auto delete + re-fetch button
    """
    user_id = message.from_user.id
    user = get_user(user_id)
    settings = get_settings()
    now = datetime.utcnow()

    # 1) Force-subscribe check
    ok = await check_and_handle_force_sub(
        client=client,
        user_id=user_id,
        wait_msg=wait_msg,
        file_code=file_code,
    )
    if not ok:
        return

    # 2) Premium vs verification
    is_premium = user.get("is_premium") and user.get("premium_until") and user["premium_until"] > now

    if not is_premium:
        # Not premium → need verification
        is_verified = user.get("is_verified") and user.get("verified_until") and user["verified_until"] > now

        if not is_verified:
            # Show verification template
            token = generate_verification_token(user_id)
            kb = verification_kb(token, settings["verify_link"])
            await wait_msg.edit_text(
                "🔐 Verification required before downloading.\n"
                "Tap **VERIFY NOW** or watch the guide.",
                reply_markup=kb,
            )
            return

        # Verified but check download limit
        if user.get("downloads_left", 0) <= 0:
            token = generate_verification_token(user_id)
            kb = verification_kb(token, settings["verify_link"])
            await wait_msg.edit_text(
                "⚠ You have used all free downloads for this verification.\n"
                "Please verify again to continue.",
                reply_markup=kb,
            )
            return

        # Decrement remaining free downloads
        update_user(user_id, {"downloads_left": user.get("downloads_left", 0) - 1})

    # 3) Send file
    caption = build_file_caption(
        settings["zip_password"],
        settings["delete_time_minutes"],
    )

    try:
        sent = await client.send_document(
            chat_id=message.chat.id,
            document=TEST_FILE_ID,
            caption=caption,
        )
        # Remove "please wait" message
        await wait_msg.delete()

        # Schedule auto-delete
        if settings["delete_time_minutes"] > 0:
            asyncio.create_task(
                delete_file_later(
                    client,
                    sent.chat.id,
                    sent.id,
                    settings["delete_time_minutes"],
                    file_code,
                )
            )

    except Exception as e:
        await wait_msg.edit_text(
            f"❌ Failed to send file. Please check TEST_FILE_ID.\n`{e}`"
        )


async def delete_file_later(
    client: Client,
    chat_id: int,
    msg_id: int,
    minutes: int,
    file_code: str,
):
    """
    Deletes the file after X minutes, and sends a message with
    'Click Here' to re-get it.
    """
    await asyncio.sleep(minutes * 60)
    try:
        await client.delete_messages(chat_id, msg_id)
    except Exception:
        pass

    await client.send_message(
        chat_id=chat_id,
        text=(
            "🗑 𝘗𝘳𝘦𝘷𝘪𝘰𝘶𝘴 𝘧𝘪𝘭𝘦 𝘮𝘦𝘴𝘴𝘢𝘨𝘦 𝘩𝘢𝘴 𝘣𝘦𝘦𝘯 𝘥𝘦𝘭𝘦𝘵𝘦𝘥.\n"
            "𝘛𝘢𝘱 𝘵𝘩𝘦 𝘣𝘶𝘵𝘵𝘰𝘯 𝘣𝘦𝘭𝘰𝘸 𝘵𝘰 𝘨𝘦𝘵 𝘪𝘵 𝘢𝘨𝘢𝘪𝘯."
        ),
        reply_markup=deleted_message_kb(file_code),
    )


# ───────────────────────── Callbacks ─────────────────────────


@app.on_callback_query()
async def callbacks(client: Client, cq: CallbackQuery):
    data = cq.data or ""
    user_id = cq.from_user.id

    # 1) Re-file after auto-delete
    if data.startswith("refile:"):
        encoded = data.split(":", 1)[1]
        decoded = b64_decode(encoded)
        if decoded.startswith("file_"):
            file_code = decoded.split("_", 1)[1]
            wait = await cq.message.reply_text("⏳ " + italic("Please wait…"))
            await handle_file_request(client, cq.message, wait, file_code)
        await cq.answer()
        return

    # 2) Force-sub "Try Again"
    if data.startswith("retry_file:"):
        encoded = data.split(":", 1)[1]
        decoded = b64_decode(encoded)
        if decoded.startswith("file_"):
            file_code = decoded.split("_", 1)[1]
            wait = await cq.message.reply_text("⏳ " + italic("Please wait…"))
            await handle_file_request(client, cq.message, wait, file_code)
        await cq.answer()
        return

    # 3) Close button (generic)
    if data == "close_msg":
        try:
            await cq.message.delete()
        except Exception:
            pass
        await cq.answer()
        return

    # 4) Verification callback
    if data.startswith("verify:"):
        encoded = data.split(":", 1)[1]
        token = decode_verification_token(encoded)
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
                "✅ Verification successful!\n"
                "Now go back to the post in the group and tap **DOWNLOAD** again."
            )
        else:
            await cq.message.edit_text(
                "❌ Bypass detected.\n"
                "Please open the original shortener link and complete all steps."
            )
        await cq.answer()
        return

    # 5) Main menu callbacks
    if data == "menu_get_file":
        await cq.answer(
            "Use the DOWNLOAD button in the public group posts to request files.",
            show_alert=True,
        )
        return

    if data == "menu_help":
        await cq.answer("Use /help to see how to use the bot.", show_alert=True)
        return

    # 6) Premium menu
    if data == "menu_premium":
        settings = get_settings()
        amount = 50  # example fixed amount; you can change
        order_id = create_payment(user_id, "Premium", amount)
        upi_uri = build_upi_uri(amount, order_id)
        qr_buf = generate_qr_png(upi_uri)

        await cq.message.reply_photo(
            photo=qr_buf,
            caption=(
                "💎 **Premium Payment**\n\n"
                f"Plan: `Premium`\n"
                f"Order ID: `{order_id}`\n"
                f"Amount: `{amount}` INR\n\n"
                "1️⃣ Scan this QR with any UPI app\n"
                "2️⃣ Complete the payment\n"
                "3️⃣ Tap **I've Paid, Verify Payment** below\n"
            ),
            reply_markup=premium_menu_kb(order_id),
        )
        await cq.answer()
        return

    # 7) Premium payment verification (FULL)
    if data.startswith("pay_verify:"):
        order_id = data.split(":", 1)[1]
        settings = get_settings()
        prem_minutes = settings["premium_minutes"]

        # In FULL mode we directly mark as paid
        premium_until = mark_payment_paid(order_id, prem_minutes)
        if premium_until:
            await cq.message.edit_caption(
                caption=(
                    "✅ **Payment Verified!**\n\n"
                    f"Premium active until: `{premium_until}`\n\n"
                    "You can now download files without verification or limits "
                    "(while premium is active)."
                ),
                reply_markup=premium_menu_kb(),
            )
        else:
            await cq.answer(
                "Payment not found or already processed.",
                show_alert=True,
            )
        return


# ───────────────────────── Admin Commands ─────────────────────────


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
        "/stats - Show user statistics\n"
        "/settings - Show current settings\n"
        "/set <key> <value> - Update a setting\n\n"
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

    int_keys = [
        "delete_time_minutes",
        "verification_days",
        "free_downloads",
        "premium_minutes",
    ]
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
