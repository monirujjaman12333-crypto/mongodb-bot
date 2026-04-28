import logging
import random
import json
import os
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, CopyTextButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.error import TimedOut, NetworkError

# ================= CONFIG =================
BOT_TOKEN = "8369733496:AAFu8IsP_H3kitEurVcC-xPoej2T9rtVeAA"
ADMIN_ID = 7526594577
SUPPORT_USERNAME = "@m_muin"
OTP_GROUP_ID = -1003221166532
MIN_WITHDRAW = 1.0

import db as _db

logging.basicConfig(level=logging.WARNING)

default_db = {
    "🔵 Facebook New": {
        "🇵🇰 Pakistan": [], "🇧🇯 Benin": [], "🇳🇵 Nepal": [], "🇧🇷 Brazil": [],
        "🇨🇳 China": [], "🇲🇦 Morocco": [], "🇮🇱 Israel": [], "🇬🇭 Ghana": [],
        "🇸🇦 Saudi Arabia": [], "🇪🇬 Egypt": [], "🇹🇿 Tanzania": [],
        "🇸🇳 Senegal": [], "🇲🇲 Myanmar": [], "🇦🇫 Afghanistan": [], "🇵🇪 Peru (+51)": [],
        "🇪🇹 Ethiopia": [], "🇾🇪 Yemen": [], "🇸🇮 Slovenia": [], "🇯🇴 Jordan": [],
        "🇰🇭 Cambodia": [], "🇹🇯 Tajikistan": [], "🇧🇫 Burkina Faso (+226)": [], "🇦🇹 Austria": [],
    },
    "🖥️ Facebook Clone": {
        "🇵🇰 Pakistan": [], "🇳🇵 Nepal": [], "🇰🇭 Cambodia": [], "🇧🇷 Brazil": [], "🇹🇯 Tajikistan": [],
        "🇧🇯 Benin": [], "🇨🇳 China": [], "🇲🇦 Morocco": [], "🇸🇦 Saudi Arabia": [],
        "🇪🇬 Egypt": [], "🇹🇿 Tanzania": [], "🇸🇳 Senegal": [], "🇬🇭 Ghana": [],
        "🇲🇲 Myanmar": [], "🇮🇱 Israel": [], "🇦🇫 Afghanistan": [], "🇪🇹 Ethiopia": [],
        "🇵🇪 Peru (+51)": [], "🇸🇮 Slovenia": [], "🇯🇴 Jordan": [],
        "🇧🇫 Burkina Faso (+226)": [], "🇦🇹 Austria": [],
    },
    "📸 Instagram": {
        "🇵🇰 Pakistan": [], "🇳🇵 Nepal": [], "🇧🇷 Brazil": [], "🇨🇳 China": [],
        "🇲🇦 Morocco": [], "🇸🇦 Saudi Arabia": [], "🇪🇬 Egypt": [], "🇬🇭 Ghana": [],
        "🇹🇿 Tanzania": [], "🇲🇲 Myanmar": [], "🇦🇫 Afghanistan": [], "🇪🇹 Ethiopia": [],
        "🇵🇪 Peru (+51)": [], "🇯🇴 Jordan": [], "🇹🇯 Tajikistan": [],
    },
    "🎵 TikTok": {
        "🇵🇰 Pakistan": [], "🇳🇵 Nepal": [], "🇧🇷 Brazil": [], "🇨🇳 China": [],
        "🇲🇦 Morocco": [], "🇸🇦 Saudi Arabia": [], "🇪🇬 Egypt": [], "🇬🇭 Ghana": [],
        "🇹🇿 Tanzania": [], "🇲🇲 Myanmar": [], "🇦🇫 Afghanistan": [], "🇪🇹 Ethiopia": [],
        "🇵🇪 Peru (+51)": [], "🇯🇴 Jordan": [],
    },
    "💚 WhatsApp": {
        "🇵🇰 Pakistan": [], "🇳🇵 Nepal": [], "🇧🇷 Brazil": [], "🇨🇳 China": [],
        "🇲🇦 Morocco": [], "🇸🇦 Saudi Arabia": [], "🇪🇬 Egypt": [], "🇬🇭 Ghana": [],
        "🇹🇿 Tanzania": [], "🇲🇲 Myanmar": [], "🇦🇫 Afghanistan": [], "🇪🇹 Ethiopia": [],
        "🇵🇪 Peru (+51)": [], "🇯🇴 Jordan": [], "🇹🇯 Tajikistan": [],
    },
    "🔐 OTP Work": {
        "🇵🇰 Pakistan": [], "🇳🇵 Nepal": [], "🇧🇷 Brazil": [], "🇨🇳 China": [],
        "🇲🇦 Morocco": [], "🇸🇦 Saudi Arabia": [], "🇪🇬 Egypt": [], "🇬🇭 Ghana": [],
        "🇹🇿 Tanzania": [], "🇲🇲 Myanmar": [], "🇦🇫 Afghanistan": [], "🇪🇹 Ethiopia": [],
        "🇵🇪 Peru (+51)": [], "🇯🇴 Jordan": [],
    },
}

numbers_db = {}
used_stats = {}
users_data = {}
active_numbers = {}



def save_data():
    _db.save_numbers(numbers_db)
    _db.save_used_stats(used_stats)
    _db.save_users(users_data, active_numbers)

def load_data():
    global numbers_db, used_stats, users_data, active_numbers
    numbers_db = _db.load_numbers()
    if not numbers_db:
        numbers_db = json.loads(json.dumps(default_db))
    for platform, countries in default_db.items():
        numbers_db.setdefault(platform, {})
        for c in countries:
            numbers_db[platform].setdefault(c, [])
    used_stats = _db.load_used_stats() or {}
    users_data, active_numbers = _db.load_users()
    # active_numbers rebuild করো
    active_numbers = {}
    for uid, u in users_data.items():
        for t in u.get("tracked_numbers", []):
            if t.get("status") in ("waiting", "received"):
                active_numbers[t["number"]] = int(uid)
        if not u.get("tracked_numbers") and u.get("active_number"):
            active_numbers[u["active_number"]] = int(uid)
    save_data()

def load_users_fresh():
    global users_data, active_numbers
    try:
        users_data, _ = _db.load_users()
        active_numbers = {}
        for uid, u in users_data.items():
            for t in u.get("tracked_numbers", []):
                if t.get("status") in ("waiting", "received"):
                    active_numbers[t["number"]] = int(uid)
            if not u.get("tracked_numbers") and u.get("active_number"):
                active_numbers[u["active_number"]] = int(uid)
    except Exception as e:
        print(f"load_users_fresh error: {e}")

def get_user(user_id):
    load_users_fresh()
    uid = str(user_id)
    if uid not in users_data:
        users_data[uid] = {
            "balance": 0.0,
            "total_earned": 0.0,
            "withdraw_requests": [],
            "active_number": None,
            "active_platform": None,
            "active_country": None,
            "active_usdt": 0.0,
            "waiting_otp": False,
            "otp_count": 0,
            "old_numbers": [],
            "tracked_numbers": [],
        }
    if "old_numbers" not in users_data[uid]:
        users_data[uid]["old_numbers"] = []
    if "tracked_numbers" not in users_data[uid]:
        users_data[uid]["tracked_numbers"] = []
    return users_data[uid]

async def safe_answer(query, text=None, alert=False):
    if query:
        try:
            await query.answer(text=text, show_alert=alert)
        except:
            pass

def main_keyboard(user_id=None):
    keyboard = [
        [KeyboardButton("📱 Get Number"), KeyboardButton("💰 Balance")],
        [KeyboardButton("💸 Withdraw"), KeyboardButton("📊 Status")],
        [KeyboardButton("🆘 Support"), KeyboardButton("⚙️ Admin")] if user_id == ADMIN_ID else [KeyboardButton("🆘 Support")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def numbers_match_score(masked, full):
    m = re.sub(r'[^\d*]', '', str(masked))
    f = re.sub(r'[^\d]', '', str(full))
    if m == f:
        return 10000
    star_idx = m.find('*')
    if star_idx == -1:
        return 0
    prefix = m[:star_idx]
    suffix = m[m.rfind('*') + 1:]
    stars  = m[star_idx: m.rfind('*') + 1]
    star_count = stars.count('*')
    expected_len = len(prefix) + len(suffix) + star_count
    if len(f) != expected_len:
        return 0
    if not f.startswith(prefix):
        return 0
    if suffix and not f.endswith(suffix):
        return 0
    return len(prefix) + len(suffix)

def parse_otp_message(text):
    number, otp = None, None
    num_match = re.search(r'Number:\s*([+\d\*\s]+)', text)
    if num_match:
        number = num_match.group(1).strip()
    otp_match = re.search(r'OTP\s*Code:\s*(\d+)', text)
    if otp_match:
        otp = otp_match.group(1).strip()
    return number, otp

async def send_main_menu(bot, chat_id, user_id):
    if user_id == ADMIN_ID:
        keyboard = [
            [InlineKeyboardButton("📞 Get Number", callback_data="get_number")],
            [InlineKeyboardButton("➕ Add Number", callback_data="add_number"),
             InlineKeyboardButton("❌ Remove Number", callback_data="remove_number")],
            [InlineKeyboardButton("👥 Admin Stats", callback_data="admin_stats")],
            [InlineKeyboardButton("👤 User List", callback_data="admin_users::0"),
             InlineKeyboardButton("💸 Withdraws", callback_data="admin_withdraws")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        ]
    else:
        keyboard = [[InlineKeyboardButton("📞 Get Number", callback_data="get_number")]]
    await bot.send_message(
        chat_id,
        "🏠 *Main Menu*\n\nWelcome! Use the buttons below.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

CHANNEL_USERNAME = "@fb_work_hub"  # ← আপনার channel username দিন

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = get_user(user.id)
    u["first_name"] = user.first_name or ""
    u["last_name"] = user.last_name or ""
    u["username"] = user.username or ""
    save_data()

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/fb_work_hub")],
        [InlineKeyboardButton("✅ Verify", callback_data="verify_join")]
    ])
    await update.message.reply_text(
        "Please Join Channel Fast And Click Verify:",
        reply_markup=keyboard
    )

async def verify_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await safe_answer(q)
    user_id = q.from_user.id
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ("member", "administrator", "creator"):
            user = get_user(user_id)
            await q.edit_message_text(
                f"👋 Welcome *{q.from_user.first_name}*!\n\nUse the menu below.",
                parse_mode="Markdown"
            )
            await send_main_menu(context.bot, q.message.chat.id, user_id)
            await context.bot.send_message(
                q.message.chat.id,
                "✅ Verified!",
                reply_markup=main_keyboard(user_id)
            )
        else:
            await safe_answer(q, "❌ আগে channel join করুন!", True)
    except Exception:
        await safe_answer(q, "❌ আগে channel join করুন!", True)

async def handle_otp_group_message(update, context):
    msg = update.message or update.channel_post
    if not msg:
        return
    text = msg.text or msg.caption or ""
    if not text:
        return
    msg_number, otp_code = parse_otp_message(text)
    if not msg_number or not otp_code:
        return

    best_score = 0
    matched_uid = None
    matched_key = None
    for stored_num, uid in list(active_numbers.items()):
        score = numbers_match_score(msg_number, stored_num)
        if score > best_score:
            best_score = score
            matched_uid = uid
            matched_key = stored_num

    if not matched_uid or best_score == 0:
        return

    user = get_user(matched_uid)
    tracked = user.get("tracked_numbers", [])

    for t in tracked:
        if t["number"] == matched_key:
            # Same OTP duplicate check
            received_otps = t.get("received_otps", [])
            if otp_code and otp_code in received_otps:
                return  # same OTP আগে এসেছে, ignore
            # নতুন OTP — save করো
            if otp_code:
                received_otps.append(otp_code)
                t["received_otps"] = received_otps
                t["last_otp"] = otp_code
            t["status"] = "received"
            # active_numbers থেকে সরাবো না — পরের OTP ও match হওয়ার জন্য
            break

    # শুধু waiting_otp আপডেট, active_numbers অক্ষত রাখো
    if user.get("active_number") == matched_key:
        user["waiting_otp"] = False

    save_data()

async def show_platform_menu_msg(message):
    """Message থেকে platform menu — শুধু যেগুলোতে number আছে"""
    buttons = []
    for idx, (platform, countries) in enumerate(numbers_db.items()):
        total = sum(len(nums) for nums in countries.values())
        if total > 0:
            buttons.append([InlineKeyboardButton(
                f"{platform}   {total} ",
                callback_data=f"platform::{idx}"
            )])
    if not buttons:
        buttons = [[InlineKeyboardButton("❌ No numbers available", callback_data="noop")]]
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="back_main")])
    await message.reply_text(
        "🎯 *Choose Platform:*",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )

async def handle_keyboard_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    if chat_id == OTP_GROUP_ID:
        await handle_otp_group_message(update, context)
        return

    if text == "📱 Get Number":
        await show_platform_menu_msg(update.message)

    elif text == "💰 Balance":
        user = get_user(update.effective_user.id)
        await update.message.reply_text(
            f"💰 *Your Balance*\n\n"
            f"💵 Current: `{user['balance']:.4f}` USDT\n"
            f"📈 Total Earned: `{user['total_earned']:.4f}` USDT\n"
            f"📲 OTPs Received: `{user.get('otp_count', 0)}`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💸 Withdraw", callback_data="withdraw_menu")]]),
            parse_mode="Markdown"
        )

    elif text == "💸 Withdraw":
        await show_withdraw_menu(update, context)

    elif text == "📊 Status":
        user = get_user(update.effective_user.id)
        tracked = user.get("tracked_numbers", [])

        if tracked:
            lines = ["📊 *Your Status*\n"]
            for i, t in enumerate(tracked[-6:], 1):
                st = t.get("status", "waiting")
                if st == "received":
                    received_otps = t.get("received_otps", [])
                    otp_count = len(received_otps)
                    # সব OTP আলাদা লাইনে দেখাবে
                    otp_lines = "\n".join([f"│ 🔑 OTP {j}: `{o}`" for j, o in enumerate(received_otps, 1)])
                    status_text = f"✅ OTP Received ({otp_count}x)" if otp_count > 1 else "✅ OTP Received"
                    lines.append(
                        f"┌─────────────────\n"
                        f"│ 📲 *Number {i}:* `{t['number']}`\n\n"
                        f"{otp_lines}\n\n"   # ← সব OTP এখন দেখাবে
                        f"│ 🌍 {t.get('country', '-')} ({t.get('platform', '-')})\n"
                        f"│ 💰 {t.get('usdt', 0)} USDT | {status_text}\n"
                        f"└─────────────────"
                    )
                else:
                    lines.append(
                        f"┌─────────────────\n"
                        f"│ 📲 *Number {i}:* `{t['number']}`\n"
                        f"│ 🌍 {t.get('country', '-')} ({t.get('platform', '-')})\n"
                        f"│ 💰 {t.get('usdt', 0)} USDT | ⏳ Waiting for OTP...\n"
                        f"└─────────────────"
                    )
            num_section = "\n\n".join(lines)
        elif user.get("active_number"):
            waiting = user.get("waiting_otp", False)
            earn = user.get("active_usdt", 0.0)
            status_icon = "⏳ Waiting for OTP..." if waiting else "✅ OTP Received"
            num_section = (
                f"📊 *Your Status*\n\n"
                f"*1.* `{user['active_number']}`\n"
                f"   🌍 {user.get('active_country', '-')} ({user.get('active_platform', '-')})\n"
                f"   💰 {earn} USDT | 📡 {status_icon}"
            )
        else:
            num_section = "📊 *Your Status*\n\n❌ No active number"

        await update.message.reply_text(
            f"{num_section}\n\n"
            f"💰 Balance: `{user['balance']:.4f}` USDT\n"
            f"📲 OTPs: `{user.get('otp_count', 0)}`\n"
            f"📈 Total Earned: `{user['total_earned']:.4f}` USDT",
            parse_mode="Markdown"
        )

    elif text == "⚙️ Admin":
        if update.effective_user.id != ADMIN_ID:
            return
        await send_main_menu(context.bot, update.effective_chat.id, update.effective_user.id)

    elif text == "🆘 Support":
        await update.message.reply_text(
            "🆘 *Support*\n\n👉 Contact us if you have any problem:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👤 Contact Support", url=f"https://t.me/{SUPPORT_USERNAME.replace('@','')}")]
            ]),
            parse_mode="Markdown"
        )
    else:
        await handle_text(update, context)

async def show_withdraw_menu(update, context):
    user = get_user(update.effective_user.id)
    balance = user["balance"]
    if balance < MIN_WITHDRAW:
        await update.message.reply_text(
            f"💸 *Withdraw*\n\n"
            f"💵 Balance: `{balance:.4f}` USDT\n"
            f"⚠️ Minimum: `{MIN_WITHDRAW}` USDT\n\n"
            f"Keep earning OTPs!",
            parse_mode="Markdown"
        )
    else:
        keyboard = [
            [InlineKeyboardButton("📱 bKash", callback_data="withdraw_method::bkash"),
             InlineKeyboardButton("🟡 Binance UID", callback_data="withdraw_method::binance")],
        ]
        await update.message.reply_text(
            f"💸 *Withdraw*\n\n"
            f"💵 Balance: `{balance:.4f}` USDT\n\n"
            f"💳 Choose payment method:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def withdraw_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await safe_answer(q)
    user = get_user(q.from_user.id)
    balance = user["balance"]
    if balance < MIN_WITHDRAW:
        await q.edit_message_text(
            f"💸 *Withdraw*\n\n💵 Balance: `{balance:.4f}` USDT\n⚠️ Minimum: `{MIN_WITHDRAW}` USDT",
            parse_mode="Markdown"
        )
    else:
        keyboard = [
            [InlineKeyboardButton("📱 bKash", callback_data="withdraw_method::bkash"),
             InlineKeyboardButton("🟡 Binance UID", callback_data="withdraw_method::binance")],
        ]
        await q.edit_message_text(
            f"💸 *Withdraw*\n\n"
            f"💵 Balance: `{balance:.4f}` USDT\n\n"
            f"💳 Payment method বেছে নাও:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def withdraw_method_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await safe_answer(q)
    method = q.data.split("::")[1]
    context.user_data["withdraw_method"] = method
    context.user_data["awaiting_withdraw"] = "amount"
    user = get_user(q.from_user.id)
    balance = user["balance"]
    method_label = "📱 bKash" if method == "bkash" else "🟡 Binance UID"
    await q.edit_message_text(
        f"💸 *Withdraw via {method_label}*\n\n"
        f"💵 Balance: `{balance:.4f}` USDT\n\n"
        f"✍️ How much USDT do you want to withdraw? (Enter the amount)\n"
        f"_(Maximum: {balance:.4f} USDT)_",
        parse_mode="Markdown"
    )

async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_answer(update.callback_query)

async def admin_user_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await safe_answer(q)
    if q.from_user.id != ADMIN_ID:
        return
    load_users_fresh()
    try:
        page = int(q.data.split("::")[1])
    except Exception:
        page = 0
    per_page = 8
    user_list = list(users_data.items())
    total = len(user_list)
    back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_main")]])
    if total == 0:
        try:
            await q.edit_message_text("👤 User List\n\n❌ কোনো user নেই!", reply_markup=back_kb)
        except Exception:
            await context.bot.send_message(q.message.chat.id, "👤 User List\n\n❌ কোনো user নেই!", reply_markup=back_kb)
        return
    start = page * per_page
    end = min(start + per_page, total)
    page_users = user_list[start:end]
    total_pages = (total - 1) // per_page + 1
    lines = [f"👤 User List | Page {page+1}/{total_pages} | Total: {total}\n"]
    buttons = []
    for uid, u in page_users:
        bal = u.get("balance", 0)
        otps = u.get("otp_count", 0)
        first = u.get("first_name", "") or ""
        last = u.get("last_name", "") or ""
        name = (first + " " + last).strip() or "Unknown"
        uname = "@" + u.get("username", "") if u.get("username") else "no username"
        lines.append(f"👤 {name} ({uname})")
        lines.append(f"🆔 {uid} | 💰 {bal:.4f} | 📲 {otps} OTP\n")
        btn_label = f"🔍 {name[:16]} …{uid[-4:]}"
        buttons.append([InlineKeyboardButton(btn_label, callback_data=f"admin_user_detail::{uid}")])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"admin_users::{page-1}"))
    if end < total:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"admin_users::{page+1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton("🔍 Search User", callback_data="admin_search_user")])
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="back_main")])
    full_text = "\n".join(lines)
    kb = InlineKeyboardMarkup(buttons)
    try:
        await q.edit_message_text(full_text, reply_markup=kb)
    except Exception as e1:
        logging.warning(f"edit_message_text failed: {e1}")
        try:
            await context.bot.send_message(q.message.chat.id, full_text, reply_markup=kb)
        except Exception as e2:
            logging.error(f"send_message also failed: {e2}")

async def admin_user_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await safe_answer(q)
    if q.from_user.id != ADMIN_ID:
        return
    uid = q.data.split("::")[1]
    load_users_fresh()
    u = users_data.get(uid, {})
    bal = u.get("balance", 0)
    earned = u.get("total_earned", 0)
    otps = u.get("otp_count", 0)
    waiting = u.get("waiting_otp", False)
    active_num = u.get("active_number") or "-"
    old_nums = u.get("old_numbers", [])
    withdraws = u.get("withdraw_requests", [])
    w_lines = []
    for w in withdraws[-3:]:
        w_lines.append(f"  • {w.get('amount', 0):.4f} USDT | {w.get('status', '?')} | {w.get('time', '')}")
    w_text = "\n".join(w_lines) if w_lines else "  কোনো withdraw নেই"
    first = u.get("first_name", "") or ""
    last = u.get("last_name", "") or ""
    name = (first + " " + last).strip() or "Unknown"
    uname = "@" + u.get("username", "") if u.get("username") else "no username"
    text = (
        f"👤 User Detail\n\n"
        f"🙍 Name: {name}\n"
        f"💬 Username: {uname}\n"
        f"🆔 ID: {uid}\n"
        f"💰 Balance: {bal:.4f} USDT\n"
        f"📈 Total Earned: {earned:.4f} USDT\n"
        f"📲 OTPs: {otps}\n"
        f"📱 Active Number: {active_num}\n"
        f"📋 Old Tracked Numbers: {len(old_nums)}\n"
        f"⏳ Waiting OTP: {waiting}\n\n"
        f"💸 Last Withdraws:\n{w_text}"
    )
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to List", callback_data="admin_users::0")]])
    try:
        await q.edit_message_text(text, reply_markup=keyboard)
    except Exception as e1:
        logging.warning(f"detail edit failed: {e1}")
        try:
            await context.bot.send_message(q.message.chat.id, text, reply_markup=keyboard)
        except Exception as e2:
            logging.error(f"detail send failed: {e2}")

async def admin_search_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await safe_answer(q)
    context.user_data["admin_searching"] = True
    try:
        await q.edit_message_text("🔍 *User Search*\n\nUser এর Telegram ID লেখো:", parse_mode="Markdown")
    except Exception:
        await q.message.reply_text("🔍 *User Search*\n\nUser এর Telegram ID লেখো:", parse_mode="Markdown")

async def admin_withdraws(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await safe_answer(q)
    if q.from_user.id != ADMIN_ID:
        return
    load_users_fresh()
    pending = []
    for uid, u in users_data.items():
        for i, w in enumerate(u.get("withdraw_requests", [])):
            if w.get("status") == "pending":
                pending.append((uid, i, w))

    async def send_or_edit(txt, kb):
        try:
            await q.edit_message_text(txt, reply_markup=kb)
        except Exception:
            try:
                await context.bot.send_message(q.message.chat.id, txt, reply_markup=kb)
            except Exception as e2:
                logging.error(f"admin_withdraws failed: {e2}")

    if not pending:
        await send_or_edit(
            "💸 Withdraw Requests\n\n✅ কোনো pending request নেই!",
            InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_main")]])
        )
        return
    def esc(s):
        s = str(s)
        for ch in ['_', '*', '`', '[']:
            s = s.replace(ch, f'\\{ch}')
        return s

    text = f"💸 Withdraw Requests ({len(pending)})\n\n"
    buttons = []
    for uid, idx, w in pending[:10]:
        u_data = users_data.get(uid, {})
        first = u_data.get("first_name", "") or ""
        last = u_data.get("last_name", "") or ""
        name = esc((first + " " + last).strip() or uid[:8])
        uname = (u_data.get("username", "") or "").replace("\\", "")
        uname_str = f"@{uname}" if uname else "no username"
        method = w.get("method", "bkash")
        method_label = "bKash" if method == "bkash" else "Binance UID"
        wallet = esc(w.get("wallet", "-"))
        amount = w.get("amount", 0)
        time_str = esc(w.get("time", ""))
        text += (
            f"👤 {name} ({uname_str})\n"
            f"🆔 {uid}\n"
            f"💵 {amount:.4f} USDT\n"
            f"💳 {method_label}: {wallet}\n"
            f"🕐 {time_str}\n\n"
        )
        buttons.append([
            InlineKeyboardButton(f"✅ Approve", callback_data=f"approve_withdraw::{uid}::{idx}"),
            InlineKeyboardButton(f"❌ Reject", callback_data=f"reject_withdraw::{uid}::{idx}")
        ])
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="back_main")])
    await send_or_edit(text, InlineKeyboardMarkup(buttons))

async def approve_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await safe_answer(q)
    if q.from_user.id != ADMIN_ID:
        return
    _, uid, idx = q.data.split("::")
    idx = int(idx)
    load_users_fresh()
    u = users_data.get(uid)
    if not u or idx >= len(u.get("withdraw_requests", [])):
        await safe_answer(q, "⚠️ Request not found", True)
        return
    w = u["withdraw_requests"][idx]
    w["status"] = "approved"
    save_data()
    try:
        ap_method = w.get("method", "bkash")
        ap_label = "📱 bKash" if ap_method == "bkash" else "🟡 Binance UID"
        await context.bot.send_message(
            int(uid),
            f"✅ *Withdraw Approved!*\n\n"
            f"💵 Amount: `{w['amount']:.4f}` USDT\n"
            f"💳 {ap_label}: `{w['wallet']}`\n\n"
            f"💸 Payment Successful!",
            parse_mode="Markdown"
        )
    except:
        pass
    method = w.get("method", "bkash")
    method_label = "📱 bKash" if method == "bkash" else "🟡 Binance UID"
    await q.edit_message_text(
        f"✅ Approved!\n\n👤 User: `{uid}`\n💵 Amount: `{w['amount']:.4f}` USDT\n💳 {method_label}: `{w['wallet']}`",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_withdraws")]]),
        parse_mode="Markdown"
    )

async def reject_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await safe_answer(q)
    if q.from_user.id != ADMIN_ID:
        return
    _, uid, idx = q.data.split("::")
    idx = int(idx)
    load_users_fresh()
    u = users_data.get(uid)
    if not u or idx >= len(u.get("withdraw_requests", [])):
        await safe_answer(q, "⚠️ Request not found", True)
        return
    w = u["withdraw_requests"][idx]
    amount = w["amount"]
    w["status"] = "rejected"
    u["balance"] = round(u.get("balance", 0) + amount, 4)
    save_data()
    try:
        await context.bot.send_message(
            int(uid),
            f"❌ *Withdraw Rejected!*\n\n"
            f"💵 Amount: `{amount:.4f}` USDT\n\n"
            f"💰 Balance refunded.\n"
            f"Balance: `{u['balance']:.4f}` USDT",
            parse_mode="Markdown"
        )
    except:
        pass
    await q.edit_message_text(
        f"❌ Rejected!\n\n👤 User: `{uid}`\n💵 `{amount:.4f}` USDT ফেরত দেওয়া হয়েছে",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_withdraws")]]),
        parse_mode="Markdown"
    )

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await safe_answer(q)
    load_users_fresh()
    total_users = len(users_data)
    total_balance = sum(u.get("balance", 0) for u in users_data.values())
    total_otps = sum(u.get("otp_count", 0) for u in users_data.values())
    total_earned = sum(u.get("total_earned", 0) for u in users_data.values())
    pending_w = sum(
        1 for u in users_data.values()
        for w in u.get("withdraw_requests", [])
        if w.get("status") == "pending"
    )
    text = (
        f"👥 *Admin Stats*\n\n"
        f"👤 Total Users: `{total_users}`\n"
        f"📲 Total OTPs: `{total_otps}`\n"
        f"💰 Unpaid Balance: `{total_balance:.4f}` USDT\n"
        f"📈 Total Earned: `{total_earned:.4f}` USDT\n"
        f"🔢 Numbers Used: `{used_stats.get('total', 0)}`\n"
        f"📡 Active Numbers: `{len(active_numbers)}`\n"
        f"💸 Pending Withdraws: `{pending_w}`"
    )
    keyboard = [
        [InlineKeyboardButton("👤 User List", callback_data="admin_users::0"),
         InlineKeyboardButton("💸 Withdraws", callback_data="admin_withdraws")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_main")]
    ]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await safe_answer(q)
    buttons = []
    for idx, (platform, countries) in enumerate(numbers_db.items()):
        total = sum(len(nums) for nums in countries.values())
        if total > 0:
            buttons.append([InlineKeyboardButton(
                f"{platform}   ({total}) ",
                callback_data=f"platform::{idx}"
            )])
    if not buttons:
        buttons = [[InlineKeyboardButton("❌ No numbers available", callback_data="noop")]]
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="back_main")])
    await q.edit_message_text(
        "🎯 *Choose Platform:*",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )

async def show_countries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await safe_answer(q)
    platform_idx = int(q.data.split("::")[1])
    platform = list(numbers_db.keys())[platform_idx]
    buttons = []
    for country_idx, (country, nums) in enumerate(numbers_db[platform].items()):
        if nums:
            usdt = nums[0]["usdt"] if nums else 0
            buttons.append([InlineKeyboardButton(
                f"{country} — {len(nums)} — 💰 ${usdt}",
                callback_data=f"country::{platform_idx}::{country_idx}"
            )])
    if not buttons:
        buttons = [[InlineKeyboardButton("❌ No numbers available", callback_data="back_main")]]
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="get_number")])
    await q.edit_message_text(f"🌍 Available countries for {platform}:", reply_markup=InlineKeyboardMarkup(buttons))

async def show_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await safe_answer(q)
    _, platform_idx, country_idx = q.data.split("::")
    platform_idx = int(platform_idx)
    country_idx = int(country_idx)
    platform = list(numbers_db.keys())[platform_idx]
    country = list(numbers_db[platform].keys())[country_idx]
    user_id = q.from_user.id
    user = get_user(user_id)
    num_list = numbers_db[platform][country]

    if not num_list:
        await q.edit_message_text(
            f"❌ No numbers left for {country} ({platform})",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=f"platform::{platform_idx}")]])
        )
        return

    count = min(3, len(num_list))
    entries = random.sample(num_list, count)
    for entry in entries:
        num_list.remove(entry)

    used_stats["total"] = used_stats.get("total", 0) + count
    key = f"{platform}_{country}"
    used_stats[key] = used_stats.get(key, 0) + count

    if "tracked_numbers" not in user:
        user["tracked_numbers"] = []

    keys_to_remove = [k for k, v in list(active_numbers.items()) if v == user_id]
    for k in keys_to_remove:
        del active_numbers[k]

    for entry in entries:
        user["tracked_numbers"].append({
            "number": entry["number"],
            "platform": platform,
            "country": country,
            "usdt": entry["usdt"],
            "status": "waiting",
        })

    if len(user["tracked_numbers"]) > 6:
        user["tracked_numbers"] = user["tracked_numbers"][-6:]

    for t in user["tracked_numbers"]:
        if t["status"] == "waiting":
            active_numbers[t["number"]] = user_id

    user["active_number"] = entries[0]["number"]
    user["active_platform"] = platform
    user["active_country"] = country
    user["active_usdt"] = entries[0]["usdt"]
    user["waiting_otp"] = True
    save_data()

    left = len(num_list)
    used = used_stats[key]
    usdt = entries[0]["usdt"]

    keyboard = []
    for entry in entries:
        keyboard.append([
            InlineKeyboardButton(
                text=f"📱 {entry['number']}",
                copy_text=CopyTextButton(text=entry["number"])
            )
        ])
    keyboard.append([
        InlineKeyboardButton("🔁 Change Number", callback_data=f"country::{platform_idx}::{country_idx}"),
        InlineKeyboardButton("📲 OTP Group", url="https://t.me/fb_otpgroup")
    ])
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"platform::{platform_idx}")])

    numbers_text = "\n".join([f"✅ *Number {i}:* `{e['number']}`" for i, e in enumerate(entries, 1)])

    await q.edit_message_text(
        f"🌍 {country} ({platform})\n"
        f"✅ Used: {used} | 📦 Left: {left} | 🔢 Total: {left + used}\n\n"
        f"💰 You will get *{usdt} USDT* for each OTP! 🤑\n\n"
        f"⏳ *Wait 10 seconds  OTP come your inbox....*\n\n"
        f"{numbers_text}\n",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def add_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id != ADMIN_ID:
        await safe_answer(q, "⚠️ Only admin allowed", True)
        return
    await safe_answer(q)
    buttons = [
        [InlineKeyboardButton(platform, callback_data=f"admin_platform::{idx}")]
        for idx, platform in enumerate(numbers_db.keys())
    ]
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="back_main")])
    await q.edit_message_text("➕ Select platform to add numbers:", reply_markup=InlineKeyboardMarkup(buttons))

async def admin_country_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await safe_answer(q)
    platform_idx = int(q.data.split("::")[1])
    platform = list(numbers_db.keys())[platform_idx]
    buttons = [
        [InlineKeyboardButton(c, callback_data=f"admin_country::{platform_idx}::{country_idx}")]
        for country_idx, c in enumerate(numbers_db[platform].keys())
    ]
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="add_number")])
    await q.edit_message_text(f"Select country for {platform}:", reply_markup=InlineKeyboardMarkup(buttons))

async def admin_save_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await safe_answer(q)
    _, platform_idx, country_idx = q.data.split("::")
    platform_idx = int(platform_idx)
    country_idx = int(country_idx)
    platform = list(numbers_db.keys())[platform_idx]
    country = list(numbers_db[platform].keys())[country_idx]
    context.user_data["adding_number"] = (platform, country)
    context.user_data["adding_step"] = "usdt"
    context.user_data["adding_platform_idx"] = platform_idx
    context.user_data["adding_country_idx"] = country_idx
    await q.edit_message_text(
        f"💰 *Set USDT amount* for *{country}* ({platform})\n\n"
        f"Send the USDT amount per OTP\n_(example: `0.5`)_",
        parse_mode="Markdown"
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    if context.user_data.get("adding_step") != "numbers":
        return
    doc = update.message.document
    if not doc:
        return
    if not (doc.file_name or "").endswith(".txt"):
        await update.message.reply_text("⚠️ শুধু *.txt* file upload করো!", parse_mode="Markdown")
        return
    platform, country = context.user_data["adding_number"]
    usdt = context.user_data.get("adding_usdt", 0.0)
    await update.message.reply_text("⏳ File processing করছি...")
    try:
        file = await context.bot.get_file(doc.file_id)
        file_bytes = await file.download_as_bytearray()
        file_text = file_bytes.decode("utf-8", errors="ignore")
    except Exception as e:
        await update.message.reply_text(f"❌ File read error: {e}")
        return
    existing = {entry["number"] for entry in numbers_db[platform][country]}
    added = []
    duplicates = []
    invalid = []
    for line in file_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.match(r'^\+?\d+$', line):
            if line in existing:
                duplicates.append(line)
            else:
                numbers_db[platform][country].append({"number": line, "usdt": usdt})
                existing.add(line)
                added.append(line)
        else:
            invalid.append(line)
    if not added and not duplicates:
        await update.message.reply_text("⚠️ File এ কোনো valid number পাওয়া যায়নি!")
        return
    save_data()
    context.user_data.pop("adding_step", None)
    context.user_data.pop("adding_usdt", None)
    context.user_data.pop("adding_number", None)
    p_idx = context.user_data.pop("adding_platform_idx", 0)
    c_idx = context.user_data.pop("adding_country_idx", 0)
    msg = (
        f"✅ *{len(added)}* number(s) added!\n"
        f"🌍 {country} ({platform})\n"
        f"💰 Each earns *{usdt} USDT* per OTP"
    )
    if duplicates:
        msg += f"\n⚠️ *{len(duplicates)}* duplicate skip"
    if invalid:
        msg += f"\n❌ *{len(invalid)}* invalid line skip"
    keyboard = [
        [InlineKeyboardButton("➕ Add More", callback_data=f"admin_country::{p_idx}::{c_idx}")],
        [InlineKeyboardButton("⬅️ Back", callback_data="add_number")]
    ]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if context.user_data.get("broadcasting") and user_id == ADMIN_ID:
        context.user_data.pop("broadcasting", None)
        load_users_fresh()
        sent = 0
        failed = 0
        for uid in users_data.keys():
            try:
                await context.bot.send_message(int(uid), text, parse_mode="Markdown")
                sent += 1
            except:
                failed += 1
        await update.message.reply_text(
            f"📢 Broadcast done!\n✅ Sent: {sent}\n❌ Failed: {failed}"
        )
        return

    if context.user_data.get("admin_searching") and user_id == ADMIN_ID:
        context.user_data.pop("admin_searching", None)
        load_users_fresh()
        uid = text.strip()
        u = users_data.get(uid)
        if not u:
            await update.message.reply_text(f"❌ User `{uid}` পাওয়া যায়নি!", parse_mode="Markdown")
            return
        bal = u.get("balance", 0)
        earned = u.get("total_earned", 0)
        otps = u.get("otp_count", 0)
        withdraws = u.get("withdraw_requests", [])
        w_text = ""
        for w in withdraws[-5:]:
            w_text += f"  • {w.get('amount', 0):.4f} USDT | {w.get('status', '?')} | bKash: {w.get('wallet', '-')} | {w.get('time', '')}\n"
        if not w_text:
            w_text = "  কোনো withdraw নেই\n"
        name = (u.get("first_name", "") + " " + u.get("last_name", "")).strip() or "Unknown"
        username = "@" + u.get("username", "") if u.get("username") else "no username"
        await update.message.reply_text(
            f"👤 User Detail\n\n"
            f"🙍 Name: {name}\n"
            f"💬 Username: {username}\n"
            f"🆔 ID: {uid}\n"
            f"💰 Balance: {bal:.4f} USDT\n"
            f"📈 Total Earned: {earned:.4f} USDT\n"
            f"📲 OTPs: {otps}\n\n"
            f"💸 Withdraw History:\n{w_text}"
        )
        return

    if context.user_data.get("adding_step") == "usdt" and user_id == ADMIN_ID:
        try:
            usdt = float(text)
            if usdt <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text("⚠️ Invalid! Send a number like `0.5`", parse_mode="Markdown")
            return
        context.user_data["adding_usdt"] = usdt
        context.user_data["adding_step"] = "numbers"
        platform, country = context.user_data["adding_number"]
        await update.message.reply_text(
            f"✅ USDT set to *{usdt}*\n\n"
            f"📁 *Option 1:* একটা *.txt* file upload করো (প্রতি line এ একটা number)\n\n"
            f"✍️ *Option 2:* সরাসরি numbers paste করো (one per line)",
            parse_mode="Markdown"
        )
        return

    if context.user_data.get("adding_step") == "numbers" and user_id == ADMIN_ID:
        platform, country = context.user_data["adding_number"]
        usdt = context.user_data.get("adding_usdt", 0.0)
        existing = {entry["number"] for entry in numbers_db[platform][country]}
        added = []
        duplicates = []
        for line in text.splitlines():
            line = line.strip()
            if re.match(r'^\+?\d+$', line):
                if line in existing:
                    duplicates.append(line)
                else:
                    numbers_db[platform][country].append({"number": line, "usdt": usdt})
                    existing.add(line)
                    added.append(line)
        if not added and not duplicates:
            await update.message.reply_text("⚠️ No valid numbers found!", parse_mode="Markdown")
            return
        save_data()
        context.user_data.pop("adding_step", None)
        context.user_data.pop("adding_usdt", None)
        context.user_data.pop("adding_number", None)
        p_idx = context.user_data.pop("adding_platform_idx", 0)
        c_idx = context.user_data.pop("adding_country_idx", 0)
        msg = f"✅ *{len(added)}* number(s) added to {country} ({platform})\n💰 Each earns *{usdt} USDT* per OTP"
        if duplicates:
            msg += f"\n\n⚠️ *{len(duplicates)}* duplicate skip হয়েছে"
        keyboard = [
            [InlineKeyboardButton("➕ Add More", callback_data=f"admin_country::{p_idx}::{c_idx}")],
            [InlineKeyboardButton("⬅️ Back", callback_data="add_number")]
        ]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    if context.user_data.get("awaiting_withdraw") == "amount":
        user = get_user(user_id)
        balance = user["balance"]
        try:
            amount = float(text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text("⚠️ সঠিক সংখ্যা লেখো! যেমন: `2.5`", parse_mode="Markdown")
            return
        if amount > balance:
            await update.message.reply_text(f"❌ Balance কম!\n💵 Available: `{balance:.4f}` USDT", parse_mode="Markdown")
            return
        if amount < MIN_WITHDRAW:
            await update.message.reply_text(f"❌ Minimum withdraw: `{MIN_WITHDRAW}` USDT", parse_mode="Markdown")
            return
        method = context.user_data.get("withdraw_method", "bkash")
        context.user_data["withdraw_amount"] = amount
        context.user_data["awaiting_withdraw"] = "wallet"
        if method == "bkash":
            await update.message.reply_text(
                f"✅ Amount: *{amount} USDT*\n\n📱 Now enter your *bKash number*:",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"✅ Amount: *{amount} USDT*\n\n🟡 Now enter your *Binance UID*:",
                parse_mode="Markdown"
            )
        return

    if context.user_data.get("awaiting_withdraw") == "wallet":
        user = get_user(user_id)
        balance = user["balance"]
        amount = context.user_data.get("withdraw_amount", 0)
        method = context.user_data.get("withdraw_method", "bkash")
        wallet = text
        username = user.get("username", "")
        uname_str = f"@{username}" if username else "no username"
        first = user.get("first_name", "") or ""
        last = user.get("last_name", "") or ""
        name = (first + " " + last).strip() or "Unknown"
        if amount > balance:
            await update.message.reply_text(f"❌ Balance কম! Available: `{balance:.4f}` USDT", parse_mode="Markdown")
            context.user_data.pop("awaiting_withdraw", None)
            context.user_data.pop("withdraw_amount", None)
            context.user_data.pop("withdraw_method", None)
            return
        user["balance"] = round(balance - amount, 4)
        request = {
            "wallet": wallet,
            "method": method,
            "amount": amount,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "status": "pending"
        }
        user["withdraw_requests"].append(request)
        save_data()
        context.user_data.pop("awaiting_withdraw", None)
        context.user_data.pop("withdraw_amount", None)
        context.user_data.pop("withdraw_method", None)
        method_label = "📱 bKash" if method == "bkash" else "🟡 Binance UID"
        wallet_label = "bKash" if method == "bkash" else "Binance UID"
        await update.message.reply_text(
            f"✅ *Withdraw Requested!*\n\n"
            f"💳 Method: {method_label}\n"
            f"💵 Amount: `{amount:.4f}` USDT\n"
            f"{wallet_label}: `{wallet}`\n"
            f"💰 Remaining Balance: `{user['balance']:.4f}` USDT\n\n"
            f"⏳ Admin will process it soon.",
            parse_mode="Markdown"
        )
        await context.bot.send_message(
            ADMIN_ID,
            f"💸 *New Withdraw Request*\n\n"
            f"👤 Name: {name}\n"
            f"💬 Username: {uname_str}\n"
            f"🆔 User ID: `{user_id}`\n"
            f"💳 Method: {method_label}\n"
            f"💵 Amount: `{amount:.4f}` USDT\n"
            f"{wallet_label}: `{wallet}`\n"
            f"💰 Remaining: `{user['balance']:.4f}` USDT\n"
            f"🕐 Time: {request['time']}",
            parse_mode="Markdown"
        )
        return

async def remove_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id != ADMIN_ID:
        await safe_answer(q, "⚠️ Only admin allowed", True)
        return
    await safe_answer(q)
    buttons = [
        [InlineKeyboardButton(platform, callback_data=f"remove_platform::{idx}")]
        for idx, platform in enumerate(numbers_db.keys())
    ]
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="back_main")])
    await q.edit_message_text("❌ Select platform to remove numbers:", reply_markup=InlineKeyboardMarkup(buttons))

async def remove_country_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await safe_answer(q)
    platform_idx = int(q.data.split("::")[1])
    platform = list(numbers_db.keys())[platform_idx]
    buttons = []
    for country_idx, (country, nums) in enumerate(numbers_db[platform].items()):
        if nums:
            buttons.append([InlineKeyboardButton(f"{country} ({len(nums)})", callback_data=f"remove_country::{platform_idx}::{country_idx}")])
    if not buttons:
        buttons = [[InlineKeyboardButton("❌ No numbers available", callback_data="back_main")]]
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="remove_number")])
    await q.edit_message_text(f"🌍 Select country ({platform}):", reply_markup=InlineKeyboardMarkup(buttons))

async def remove_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await safe_answer(q)
    _, platform_idx, country_idx = q.data.split("::")
    platform_idx = int(platform_idx)
    country_idx = int(country_idx)
    platform = list(numbers_db.keys())[platform_idx]
    country = list(numbers_db[platform].keys())[country_idx]
    keyboard = [
        [InlineKeyboardButton("❌ Remove All", callback_data=f"remove_all::{platform_idx}::{country_idx}")],
        [InlineKeyboardButton("⬅️ Back", callback_data=f"remove_platform::{platform_idx}")]
    ]
    await q.edit_message_text(f"⚠️ Remove all numbers from\n{country} ({platform})?", reply_markup=InlineKeyboardMarkup(keyboard))

async def remove_all_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await safe_answer(q)
    _, platform_idx, country_idx = q.data.split("::")
    platform_idx = int(platform_idx)
    country_idx = int(country_idx)
    platform = list(numbers_db.keys())[platform_idx]
    country = list(numbers_db[platform].keys())[country_idx]
    removed = len(numbers_db[platform][country])
    numbers_db[platform][country] = []
    save_data()
    await q.edit_message_text(f"✅ {removed} numbers removed from\n{country} ({platform})")
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await safe_answer(q)
    if q.from_user.id != ADMIN_ID:
        return
    context.user_data["broadcasting"] = True
    await q.edit_message_text(
        "📢 *Broadcast Message*\n\nসব user কে যে message পাঠাতে চান সেটা লিখুন:",
        parse_mode="Markdown"
    )

async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await safe_answer(q)
    await send_main_menu(context.bot, q.message.chat.id, q.from_user.id)

async def error_handler(update, context):
    if isinstance(context.error, (TimedOut, NetworkError)):
        logging.warning("Network error")
    else:
        logging.error(context.error)

def main():
    load_data()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify_join,           pattern="^verify_join$"))
    app.add_handler(CallbackQueryHandler(broadcast,             pattern="^broadcast$"))
    app.add_handler(CallbackQueryHandler(get_number,            pattern="^get_number$"))
    app.add_handler(CallbackQueryHandler(show_countries,        pattern="^platform::"))
    app.add_handler(CallbackQueryHandler(show_number,           pattern="^country::"))
    app.add_handler(CallbackQueryHandler(add_number,            pattern="^add_number$"))
    app.add_handler(CallbackQueryHandler(remove_number,         pattern="^remove_number$"))
    app.add_handler(CallbackQueryHandler(remove_country_list,   pattern="^remove_platform::"))
    app.add_handler(CallbackQueryHandler(remove_confirm,        pattern="^remove_country::"))
    app.add_handler(CallbackQueryHandler(remove_all_numbers,    pattern="^remove_all::"))
    app.add_handler(CallbackQueryHandler(admin_country_select,  pattern="^admin_platform::"))
    app.add_handler(CallbackQueryHandler(admin_save_number,     pattern="^admin_country::"))
    app.add_handler(CallbackQueryHandler(back_main,             pattern="^back_main$"))
    app.add_handler(CallbackQueryHandler(withdraw_callback,     pattern="^withdraw_menu$"))
    app.add_handler(CallbackQueryHandler(withdraw_method_callback, pattern="^withdraw_method::"))
    app.add_handler(CallbackQueryHandler(admin_stats,           pattern="^admin_stats$"))
    app.add_handler(CallbackQueryHandler(admin_user_list,       pattern="^admin_users::"))
    app.add_handler(CallbackQueryHandler(admin_user_detail,     pattern="^admin_user_detail::"))
    app.add_handler(CallbackQueryHandler(admin_search_user,     pattern="^admin_search_user$"))
    app.add_handler(CallbackQueryHandler(admin_withdraws,       pattern="^admin_withdraws$"))
    app.add_handler(CallbackQueryHandler(approve_withdraw,      pattern="^approve_withdraw::"))
    app.add_handler(CallbackQueryHandler(reject_withdraw,       pattern="^reject_withdraw::"))
    app.add_handler(CallbackQueryHandler(noop_callback,         pattern="^noop$"))
    app.add_handler(MessageHandler(filters.Chat(chat_id=OTP_GROUP_ID), handle_otp_group_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_keyboard_buttons))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_error_handler(error_handler)
    print("🚀 Bot running...")
    app.run_polling()

# ... আগের সব code ...

import threading

def run_otp_monitor():
    try:
        import otp_monitor
        otp_monitor.main()
    except Exception as e:
        print(f"OTP Monitor error: {e}")

threading.Thread(target=run_otp_monitor, daemon=True).start()  # ← এখানে

if __name__ == "__main__":
    main()
