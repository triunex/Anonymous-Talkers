import asyncio
import json
import time
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from datetime import datetime

class DB:
    def __init__(self, db_file="database.json"):
        self.db_file = db_file
        self.data = self._load_db()

    def _load_db(self):
        try:
            with open(self.db_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def _save_db(self):
        with open(self.db_file, "w") as f:
            json.dump(self.data, f)

    def set_user_interests(self, user_id, interests):
        self.data[str(user_id)] = {"interests": interests}
        self._save_db()

    def get_user_interests(self, user_id):
        """Retrieve the interests of a user."""
        return self.data.get(str(user_id), {}).get("interests", [])

    def get_waiting_users(self):
        """Retrieve the list of waiting users."""
        return self.data.get("waiting_users", [])

    def remove_from_queue(self, user_id):
        """Remove a user from the waiting queue."""
        queue = self.data.get("waiting_users", [])
        if user_id in queue:
            queue.remove(user_id)
            self.data["waiting_users"] = queue
            self._save_db()

db = DB()

BOT_TOKEN = "7678845859:AAF-U2emUFUVztVgkcI-_vRlMA6FXJXCGdU"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

waiting_users = []
active_chats = {}
user_gender = {}
user_preference = {}
user_interests = {}
user_language = {}
blocked_users = {}
session_history = {}

PREMIUM_FILE = "premium_users.json"
VERIFIED_FILE = "verified_users.json"
NOTIFY_FILE = "notification_settings.json"

for file in [PREMIUM_FILE, VERIFIED_FILE, NOTIFY_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)

def load_json(file):
    with open(file) as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

def load_premium_users():
    return load_json(PREMIUM_FILE)

def save_premium_users(data):
    save_json(PREMIUM_FILE, data)

def is_premium(user_id):
    data = load_premium_users()
    expiry = data.get(str(user_id), 0)
    return time.time() < expiry

def make_premium(user_id, days=30):
    data = load_premium_users()
    data[str(user_id)] = time.time() + days * 86400
    save_premium_users(data)

def is_verified(user_id):
    data = load_json(VERIFIED_FILE)
    return str(user_id) in data

def set_verified(user_id):
    data = load_json(VERIFIED_FILE)
    data[str(user_id)] = True
    save_json(VERIFIED_FILE, data)

def toggle_notify(user_id):
    data = load_json(NOTIFY_FILE)
    if str(user_id) in data:
        data.pop(str(user_id))
    else:
        data[str(user_id)] = True
    save_json(NOTIFY_FILE, data)

def is_notify_enabled(user_id):
    data = load_json(NOTIFY_FILE)
    return str(user_id) not in data

toxic_keywords = ["idiot", "dumb", "stupid", "hate", "ugly"]

analytics = {
    "total_chats": 0,
    "reports": []
}

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "\n✨ *Welcome to Anonymous Chat Bot!* ✨\n\n"
        "Chat with strangers while staying anonymous.\n\n"
        "👉 /chat - Start chatting\n"
        "📛 /stop - Leave chat\n"
        "🦮 /setgender - Set your gender\n"
        "🏷 /setinterests - Set your interests\n"
        "🌐 /setlanguage - Set preferred language\n"
        "📸 /verifyme - Verify with selfie\n"
        "🔔 /notify - Toggle message notifications\n"
        "🧑‍💼 /admin - Admin panel\n"
        "💎 /upgrade - Premium matching options\n"
        "🚨 /report - Report current partner\n"
        "🚫 /block - Block current partner\n"
        "⏭ /next - Skip to next chat\n"
        "🔁 /reconnect - Reconnect last partner\n"
        "❓ /help - Show all commands",
        parse_mode="Markdown")

@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "❓ *Help Menu*\n\n"
        "👉 /chat - Start a new chat\n"
        "📛 /stop - Stop current chat\n"
        "⏭ /next - Skip to next user\n"
        "🔁 /reconnect - Reconnect last chat partner\n"
        "🦮 /setgender - Set your gender (Male/Female)\n"
        "🏷 /setinterests - Set your chat interests\n"
        "🌐 /setlanguage - Choose your preferred language\n"
        "📸 /verifyme - Verify yourself with a selfie\n"
        "💎 /upgrade - Become premium & choose who to chat with\n"
        "🚨 /report - Report your current partner\n"
        "🚫 /block - Block current chat partner\n"
        "🔔 /notify - Enable/Disable typing notification\n"
        "🧑‍💼 /admin - Admin dashboard (admin only)\n"
        "👑 /makepremium - Admin-only premium grant\n",
        parse_mode="Markdown")

@dp.message(Command("verifyme"))
async def verifyme(message: Message):
    await message.answer("📸 Please send your selfie photo now to verify yourself.")

@dp.message(Command("notify"))
async def toggle_notifications(message: Message):
    toggle_notify(message.from_user.id)
    status = "enabled" if is_notify_enabled(message.from_user.id) else "disabled"
    await message.answer(f"🔔 Message notifications {status}.")

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != 7354774428:
        await message.answer("❌ You’re not authorized.")
        return
    await message.answer(
        f"📊 *Admin Analytics*\n\nTotal Chats: {analytics['total_chats']}\nReports: {len(analytics['reports'])}",
        parse_mode="Markdown")

@dp.message(Command("setgender"))
async def set_gender(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👦 Male", callback_data="gender_male")],
        [InlineKeyboardButton(text="👧 Female", callback_data="gender_female")]
    ])
    await message.answer("🦮 Please select your gender:", reply_markup=keyboard)

@dp.message_handler(commands=["set_interests"])
async def set_interests(message: types.Message, state: FSMContext):
    await message.answer("🎯 Send your interests separated by commas (e.g. `movies, cricket, anime`):")
    await state.set_state("awaiting_interests")

@dp.message_handler(state="awaiting_interests")
async def save_interests(message: types.Message, state: FSMContext):
    interests_raw = message.text.lower()
    interests = [i.strip() for i in interests_raw.split(',') if i.strip()]
    user_id = message.from_user.id
    db.set_user_interests(user_id, interests)  # You'll implement this in DB
    await message.answer(f"✅ Interests saved: {', '.join(interests)}")
    await state.finish()

@dp.message(Command("setlanguage"))
async def set_language(message: Message):
    await message.answer("🌐 Send your preferred language (e.g., English, Hindi):")

@dp.message(Command("upgrade"))
async def upgrade(message: Message):
    await message.answer("💎 *Upgrade to Premium* 💎\n\n"
                         "Choose your chat partner’s gender.\n"
                         "Only ₹10!\n\n"
                         "🪙 Payments via PayTM, UPI & Stripe - Coming Soon!",
                         parse_mode="Markdown")

@dp.message(Command("makepremium"))
async def make_premium_handler(message: Message):
    if message.from_user.id != 7354774428:
        await message.answer("❌ You’re not authorized.")
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Usage: /makepremium <user_id> [days]")
        return
    uid = int(parts[1])
    days = int(parts[2]) if len(parts) > 2 else 30
    make_premium(uid, days)
    await message.answer(f"✅ User {uid} upgraded for {days} days.")

@dp.callback_query(lambda c: c.data.startswith("gender_"))
async def gender_callback(callback: types.CallbackQuery):
    gender = "Male" if callback.data == "gender_male" else "Female"
    user_gender[callback.from_user.id] = gender
    await callback.message.answer(f"✅ Gender set to *{gender} click to /chat to start chat*.", parse_mode="Markdown")
    await callback.answer("🎉 You’re all set! Type /chat to meet someone new.")
    await callback.answer()


@dp.message(Command("chat"))
async def chat_handler(message: Message):
    uid = message.chat.id

    if uid in active_chats:
        await message.answer("⚠️ You are already chatting. Type /stop to disconnect.")
        return

    if uid not in user_gender:
        await message.answer("❗ Please set your gender first using /setgender")
        return

    if is_premium(uid):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Chat with 👦 Male", callback_data="pref_male")],
            [InlineKeyboardButton(text="Chat with 👧 Female", callback_data="pref_female")],
            [InlineKeyboardButton(text="🔀 Random Match", callback_data="pref_any")]
        ])
        await message.answer("💎 Who do you want to chat with?", reply_markup=keyboard)
    else:
        await find_partner(uid, None)

@dp.callback_query(lambda c: c.data.startswith("pref_"))
async def handle_preference(callback: types.CallbackQuery):
    pref = callback.data.replace("pref_", "")
    user_preference[callback.from_user.id] = pref
    await callback.answer()
    await callback.message.answer("🔍 Searching for someone special for you...")
    await find_partner(callback.from_user.id, pref)

@dp.message(Command("stop"))
async def stop_chat(message: Message):
    uid = message.chat.id
    pid = active_chats.pop(uid, None)
    if pid:
        active_chats.pop(pid, None)
        session_history[uid] = pid
        await message.answer("❌ You left the chat. Type /chat to meet someone new.")
        await bot.send_message(pid, "❌ Your chat partner has disconnected. Click /chat to chat someone new")
    elif uid in waiting_users:
        waiting_users.remove(uid)
        await message.answer("🚫 You left the queue.")
    else:
        await message.answer("⚠️ You're not in a chat right now.")

@dp.message(Command("next"))
async def skip_next(message: Message):
    await stop_chat(message)
    await chat_handler(message)

@dp.message(Command("reconnect"))
async def reconnect(message: Message):
    uid = message.chat.id
    pid = session_history.get(uid)
    if pid:
        active_chats[uid] = pid
        active_chats[pid] = uid
        await message.answer("🔁 Reconnected with your last partner.")
        await bot.send_message(pid, "🔁 You’ve been reconnected with your previous partner.")
    else:
        await message.answer("⚠️ No previous session to reconnect.")

@dp.message(Command("report"))
async def report_user(message: Message):
    uid = message.chat.id
    pid = active_chats.get(uid)
    if not pid:
        await message.answer("⚠️ You're not chatting with anyone to report.")
        return

    analytics["reports"].append({
        "reporter": uid,
        "reported": pid,
        "timestamp": datetime.now().isoformat()
    })

    await message.answer("🚨 User has been reported. Thank you for helping us improve the community!")
    await bot.send_message(pid, "⚠️ You have been reported by your chat partner.")

@dp.message(Command("block"))
async def block_user(message: Message):
    uid = message.chat.id
    pid = active_chats.get(uid)
    if not pid:
        await message.answer("⚠️ You're not chatting with anyone to block.")
        return

    if uid not in blocked_users:
        blocked_users[uid] = []

    if pid not in blocked_users[uid]:
        blocked_users[uid].append(pid)

    await stop_chat(message)
    await message.answer("🚫 You blocked this user and left the chat. They won’t be matched with you again.")

@dp.message()
async def handle_all_messages(message: Message):
    uid = message.chat.id

    if message.photo and message.caption == None:
        set_verified(uid)
        await message.answer("✅ Selfie received. You’re now verified!")
        return

    text = message.text.lower() if message.text else ""

    if "," in text:
        user_interests[uid] = [i.strip().lower() for i in text.split(",")]
        await message.answer("✅ Interests saved. Click to /chat to starting chatting to your manpasand partners")
    elif text.isalpha() and text.capitalize() in ["English", "Hindi"]:
        user_language[uid] = text.capitalize()
        await message.answer(f"✅ Language set to {text.capitalize()}.")
    elif uid in active_chats:
        pid = active_chats.get(uid)
        if any(word in text for word in toxic_keywords):
            await message.answer("🚫 Your message was blocked for using inappropriate language.")
            return
        try:
            if is_notify_enabled(uid):
                await bot.send_chat_action(pid, "typing")
                await asyncio.sleep(1.2)

            prefix = "✅ [Verified] " if is_verified(uid) else "💬"

            if message.text:
                await bot.send_message(pid, f"{prefix} {message.text}")
            elif message.photo:
                await bot.send_photo(pid, photo=message.photo[-1].file_id, caption=f"{prefix} {message.caption or ''}")
            elif message.document:
                await bot.send_document(pid, document=message.document.file_id, caption=f"{prefix} {message.caption or ''}")
            elif message.video:
                await bot.send_video(pid, video=message.video.file_id, caption=f"{prefix} {message.caption or ''}")
            elif message.sticker:
                await bot.send_sticker(pid, sticker=message.sticker.file_id)
            elif message.voice:
                await bot.send_voice(pid, voice=message.voice.file_id)
            else:
                await message.answer("⚠️ File type not supported yet.")
        except Exception as e:
            await message.answer(f"⚠️ Error delivering message: {str(e)}")
    else:
        await message.answer("💬 Type /chat to connect with someone.")

def is_waiting(user_id):
    return user_id in waiting_users

def find_match(user_id):
    user_interests = db.get_user_interests(user_id)
    queue = db.get_waiting_users()

    for candidate in queue:
        if candidate == user_id:
            continue
        candidate_interests = db.get_user_interests(candidate)
        if set(user_interests) & set(candidate_interests):  # if common
            db.remove_from_queue(candidate)
            return candidate
    return None

async def find_partner(uid, pref):
    if is_waiting(uid):
        return

    premium_waiting = [u for u in waiting_users if is_premium(u)]
    normal_waiting = [u for u in waiting_users if not is_premium(u)]
    sorted_waiting = premium_waiting + normal_waiting

    for pid in sorted_waiting:
        if pid == uid or pid in active_chats or uid in blocked_users.get(pid, []):
            continue

        match_gender = (pref in [None, "any"]) or (user_gender.get(pid) == pref.capitalize())
        reverse_pref = user_preference.get(pid)
        reverse_gender_match = (reverse_pref in [None, "any"]) or (user_gender.get(uid) == reverse_pref.capitalize())

        uid_interests = set(user_interests.get(uid, []))
        pid_interests = set(user_interests.get(pid, []))
        match_interests = not uid_interests or not pid_interests or bool(uid_interests & pid_interests)

        uid_lang = user_language.get(uid)
        pid_lang = user_language.get(pid)
        match_language = not uid_lang or not pid_lang or uid_lang == pid_lang

        if match_gender and reverse_gender_match and match_interests and match_language:
            if pid in waiting_users:
                waiting_users.remove(pid)
            active_chats[uid] = pid
            active_chats[pid] = uid
            analytics["total_chats"] += 1
            await bot.send_message(uid, "✅ *You are now connected! Say hi 👋*", parse_mode="Markdown")
            await bot.send_message(pid, "✅ *You are now connected! Say hi 👋*", parse_mode="Markdown")
            return

    if is_premium(uid):
        waiting_users.insert(0, uid)
    else:
        waiting_users.append(uid)

    await bot.send_message(uid, "⏳ No match found right now. Waiting for someone...")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
