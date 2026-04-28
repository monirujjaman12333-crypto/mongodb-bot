import time
import json
import requests
import os
import re
import html
import hashlib
import db as _db

# =======================
# Configuration
# =======================
TELEGRAM_BOT_TOKEN = "8369733496:AAFu8IsP_H3kitEurVcC-xPoej2T9rtVeAA"  # ← তোমার NUMBER BOT token
TELEGRAM_CHAT_ID = "-1003221166532"   # ← OTP group ID
HADI_API_URL = "http://147.135.212.197/crapi/had/viewstats"
HADI_API_KEY = "RldTRDRSQkdngpFzh4lveGNXdl9SYIpYZmyCYXFq"
POLL_INTERVAL = 2  # seconds

def load_seen():
    return _db.load_seen()

def save_seen(seen_set):
    _db.save_seen(seen_set)

def fetch_hadi():
    try:
        resp = requests.get(HADI_API_URL, params={"token": HADI_API_KEY, "records": 500}, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print("⚠️ Hadi API error:", e)
        return None

# =======================
# OTP extraction
# =======================
OTP_RE = re.compile(r"\b(\d{4,8})\b")

def extract_otp(text):
    if not text:
        return None
    m = OTP_RE.search(text)
    return m.group(1) if m else None

# =======================
# Country & Service
# =======================
COUNTRY_CODE_NAME = {
    "93": "🇦🇫 Afghanistan", "355": "🇦🇱 Albania", "213": "🇩🇿 Algeria",
    "880": "🇧🇩 Bangladesh", "91": "🇮🇳 India", "1": "🇺🇸 United States",
    "44": "🇬🇧 United Kingdom", "82": "🇰🇷 South Korea", "66": "🇹🇭 Thailand",
    "62": "🇮🇩 Indonesia", "49": "🇩🇪 Germany", "971": "🇦🇪 UAE",
    "61": "🇦🇺 Australia", "7": "🇷🇺 Russia", "20": "🇪🇬 Egypt",
    "27": "🇿🇦 South Africa", "33": "🇫🇷 France", "34": "🇪🇸 Spain",
    "39": "🇮🇹 Italy", "43": "🇦🇹 Austria", "55": "🇧🇷 Brazil",
    "57": "🇨🇴 Colombia", "60": "🇲🇾 Malaysia", "65": "🇸🇬 Singapore",
    "81": "🇯🇵 Japan", "84": "🇻🇳 Vietnam", "86": "🇨🇳 China",
    "90": "🇹🇷 Turkey", "98": "🇮🇷 Iran", "212": "🇲🇦 Morocco",
    "233": "🇬🇭 Ghana", "229": "🇧🇯 Benin", "95": "🇲🇲 Myanmar",
    "51": "🇵🇪 Peru", "92": "🇵🇰 Pakistan", "977": "🇳🇵 Nepal",
    "855": "🇰🇭 Cambodia", "992": "🇹🇯 Tajikistan", "226": "🇧🇫 Burkina Faso",
    "251": "🇪🇹 Ethiopia", "967": "🇾🇪 Yemen", "386": "🇸🇮 Slovenia",
    "962": "🇯🇴 Jordan", "254": "🇰🇪 Kenya", "255": "🇹🇿 Tanzania",
    "221": "🇸🇳 Senegal", "972": "🇮🇱 Israel", "93": "🇦🇫 Afghanistan",
}

def infer_country(phone, country_field=None):
    if country_field:
        return country_field
    if not phone:
        return "Unknown"
    p = re.sub(r"\D", "", str(phone))
    for length in (3, 2, 1):
        code = p[:length]
        if code in COUNTRY_CODE_NAME:
            return COUNTRY_CODE_NAME[code]
    return "Unknown"

def detect_service(message, service_field=None):
    if service_field and str(service_field).strip():
        return str(service_field)
    if not message:
        return "Unknown"
    txt = message.lower()
    keywords = {
        "Facebook": ["facebook", "fb"],
        "WhatsApp": ["whatsapp"],
        "Google": ["google", "gmail"],
        "Instagram": ["instagram"],
        "Telegram": ["telegram"],
        "Twitter": ["twitter"],
        "IMO": ["imo"],
    }
    for svc, keys in keywords.items():
        for k in keys:
            if k in txt:
                return svc
    return "Unknown"

def mask_phone(phone):
    if not phone:
        return "unknown"
    p = re.sub(r"\D", "", str(phone))
    if len(p) <= 6:
        return "+" + p
    return "+" + p[:4] + "***" + p[-4:]

# =======================
# Number matching
# =======================
def numbers_match_score(stored, incoming):
    """Strict matching with score. Higher = better match. 0 = no match."""
    s = re.sub(r'[^\d*]', '', str(stored))
    i = re.sub(r'[^\d]', '', str(incoming))

    # Exact match
    if s == i:
        return 10000

    star_idx = s.find('*')
    if star_idx == -1:
        return 0

    prefix = s[:star_idx]
    suffix = s[s.rfind('*') + 1:]
    stars = s[star_idx: s.rfind('*') + 1]
    star_count = stars.count('*')

    # Strict length check: prefix + suffix + exactly star_count digits
    expected_len = len(prefix) + len(suffix) + star_count
    if len(i) != expected_len:
        return 0
    if not i.startswith(prefix):
        return 0
    if suffix and not i.endswith(suffix):
        return 0

    return len(prefix) + len(suffix)


def notify_user(raw_phone, otp):
    try:
        users, _ = _db.load_users()

        # active_numbers কে tracked_numbers থেকে rebuild করো
        active_numbers = {}
        for uid, u in users.items():
            for t in u.get("tracked_numbers", []):
                if t.get("status") in ("waiting", "received"):
                    active_numbers[t["number"]] = int(uid)
            if not u.get("tracked_numbers") and u.get("active_number"):
                active_numbers[u["active_number"]] = int(uid)

        if not active_numbers:
            print("⚠️ No active numbers found")
            return

        phone_clean = re.sub(r'[^\d]', '', str(raw_phone))

        # Best match খোঁজো — score based
        best_score = 0
        matched_uid = None
        matched_key = None

        for stored_num, uid in list(active_numbers.items()):
            score = numbers_match_score(stored_num, phone_clean)
            if score > best_score:
                best_score = score
                matched_uid = uid
                matched_key = stored_num

        if not matched_uid or best_score == 0:
            print(f"⚠️ No user found for number: {raw_phone}")
            return

        user = users.get(str(matched_uid))
        if not user:
            print(f"⚠️ User {matched_uid} not found")
            return

        # tracked_numbers এ এই number খোঁজো
        tracked = user.get("tracked_numbers", [])
        earn = 0.0
        display_number = matched_key
        found_tracked = False

        for t in tracked:
            if t["number"] == matched_key:
                received_otps = t.get("received_otps", [])
                if otp in received_otps:
                    print(f"⚠️ Same OTP duplicate ignored for {matched_key}: {otp}")
                    return  # same OTP — ignore
                # নতুন OTP — allow
                received_otps.append(otp)
                t["received_otps"] = received_otps
                t["status"] = "received"
                t["last_otp"] = otp
                earn = float(t.get("usdt", user.get("active_usdt", 0.0)))
                found_tracked = True
                break

        if not found_tracked:
            # backward compat — tracked_numbers নেই
            earn = float(user.get("active_usdt", 0.0))
            user["waiting_otp"] = False

        # Balance update
        user["balance"] = round(float(user.get("balance", 0.0)) + earn, 4)
        user["total_earned"] = round(float(user.get("total_earned", 0.0)) + earn, 4)
        user["otp_count"] = int(user.get("otp_count", 0)) + 1

        # active_numbers থেকে সরাবো না — একই number এ পরের OTP ও match হওয়ার জন্য
        if user.get("active_number") == matched_key:
            user["waiting_otp"] = False

        # Save to MongoDB
        _db.save_users(users, active_numbers)

        # OTP count দেখাও (একাধিক হলে)
        all_otps = []
        for t in tracked:
            if t["number"] == matched_key:
                all_otps = t.get("received_otps", [otp])
                break
        otp_count = len(all_otps)
        otp_count_line = f"📊 Total OTPs on this number: <b>{otp_count}x</b>\n" if otp_count > 1 else ""

        # User কে message পাঠাও
        # tracked number থেকে platform ও country বের করো
        platform_name = ""
        country_name = ""
        for t in tracked:
            if t["number"] == matched_key:
                platform_name = t.get("platform", "")
                country_name = t.get("country", "")
                break
        
        msg = (
            f"✅ <b>OTP Received!</b>\n"
            f"🌍 {country_name} ({platform_name})\n\n"
            f"┌─────────────────\n"
            f"│ 📱 Number: <code>{display_number}</code>\n\n"
            f"│ 🔑 OTP Code: <code>{otp}</code>\n"
            f"└─────────────────\n"
            f"{otp_count_line}\n"
            f"💰 Earned: <b>+{earn} USDT</b>\n"
            f"💵 New Balance: <code>{user['balance']:.4f}</code> USDT"
        )

        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": matched_uid, "text": msg, "parse_mode": "HTML"},
            timeout=15
        )

        if r.ok:
            print(f"✅ OTP sent to user {matched_uid} | Number: {display_number} | OTP: {otp} | Earned: {earn} USDT")
        else:
            print(f"⚠️ Failed to send to user {matched_uid}: {r.text}")

    except Exception as e:
        print(f"⚠️ notify_user error: {e}")

# =======================
# Telegram - send to OTP group
# =======================
def build_reply_markup():
    keyboard = [[
        {"text": "📢 Main Channel", "url": "https://t.me/fb_work_hub"},
        {"text": "🤖 NUMBER BOT", "url": "https://t.me/onlynumbarbot"}
    ]]
    return {"inline_keyboard": keyboard}

def send_to_group(text, reply_markup=None):
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data=payload, timeout=15
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Telegram group error:", e)
        return None

# =======================
# Unique ID per OTP
# =======================
def get_item_id(item):
    otp = extract_otp(item.get("message") or "")
    phone = item.get("num") or item.get("phone") or ""
    dt = item.get("dt") or item.get("time") or ""
    return hashlib.md5(f"{phone}-{otp}-{dt}".encode()).hexdigest()

# =======================
# Format group message
# =======================
def format_group_message(item):
    raw_phone = item.get("num") or item.get("phone") or ""
    message = item.get("message") or item.get("msg") or ""
    dt = item.get("dt") or item.get("time") or ""
    country_field = item.get("country") or item.get("ctry") or ""
    service_field = item.get("service") or item.get("srv") or ""

    service = detect_service(message, service_field)
    country = infer_country(raw_phone, country_field)
    phone_masked = mask_phone(raw_phone)
    otp = extract_otp(message)

    msg_esc = html.escape(message).replace("\x00", "")
    clean_sms = msg_esc.replace("\n", " ").strip()
    if len(clean_sms) > 400:
        clean_sms = clean_sms[:400] + "..."

    text = (
        "✨ <b>OTP Received</b> ✨\n\n"
        f"⏰ <b>Time:</b> {dt}\n"
        f"📱 <b>Number:</b> {phone_masked}\n"
        f"🌍 <b>Country:</b> {country}\n"
        f"🔧 <b>Service:</b> {service}\n\n"
        f"🔑 <b>OTP Code:</b> <code>{otp}</code>\n\n"
        f"💬 <b>Full Message:</b>\n<pre>{clean_sms}</pre>"
    )

    return text, otp, raw_phone

# =======================
# Init - mark existing as seen
# =======================
def init_seen():
    seen = load_seen()
    data = fetch_hadi()
    if data and data.get("status") != "error":
        for item in data.get("data", []):
            seen.add(get_item_id(item))
        save_seen(seen)
        print(f"✅ Initialized with {len(seen)} existing OTPs")
    return seen

# =======================
# Main Loop
# =======================
def main():
    print("🚀 OTP Monitor started (MongoDB mode)...")
    seen = init_seen()

    try:
        while True:
            data = fetch_hadi()
            if not data or data.get("status") == "error":
                time.sleep(POLL_INTERVAL)
                continue

            for item in data.get("data", []):
                item_id = get_item_id(item)
                if item_id in seen:
                    continue

                group_text, otp, raw_phone = format_group_message(item)

                if not otp:
                    seen.add(item_id)
                    save_seen(seen)
                    continue

                # 1. Send to OTP group
                res = send_to_group(group_text, reply_markup=build_reply_markup())

                # 2. Notify user in bot inbox
                notify_user(raw_phone, otp)

                seen.add(item_id)
                save_seen(seen)

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("🛑 Stopped.")
    except Exception as e:
        print(f"⚠️ Fatal error: {e}")

if __name__ == "__main__":
    main()
