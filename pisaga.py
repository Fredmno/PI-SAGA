import logging
import random
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = "YOUR_TOKEN_HERE"  # ← paste your token

logging.basicConfig(level=logging.INFO)

conn = sqlite3.connect("pisaga.db", check_same_thread=False)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS players (user_id INTEGER PRIMARY KEY, name TEXT, class TEXT, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1)")
conn.commit()

CLASSES = ["🧙 Mage", "🗡️ Warrior", "🏹 Ranger", "🔮 Mystic"]
SAMPLE_PUZZLES = [
    {"q": "What has keys but can't open locks?", "a": "piano"},
    {"q": "What gets wetter the more it dries?", "a": "towel"},
    {"q": "I speak without a mouth and hear without ears. What am I?", "a": "echo"},
    {"q": "What has a head and a tail but no body?", "a": "coin"},
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    c.execute("SELECT * FROM players WHERE user_id=?", (user.id,))
    if c.fetchone():
        await update.message.reply_text(f"Welcome back, {user.first_name}! 🎮\n/class - change class\n/puzzle - solve a riddle\n/profile - your stats")
        return
    keyboard = [[InlineKeyboardButton(cls, callback_data=cls.split()[-1].lower())] for cls in CLASSES]
    await update.message.reply_text("Choose your class:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    chosen = query.data.capitalize()
    c.execute("INSERT OR REPLACE INTO players (user_id, name, class, xp, level) VALUES (?, ?, ?, 0, 1)", (user.id, user.first_name, chosen))
    conn.commit()
    await query.edit_message_text(f"You are now a {chosen}! 🎮\nType /puzzle to earn XP")

async def puzzle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    puzzle = random.choice(SAMPLE_PUZZLES)
    context.user_data["answer"] = puzzle["a"]
    await update.message.reply_text(f"🧩 Riddle: {puzzle['q']}\n\nReply with your answer!")

async def answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "answer" not in context.user_data:
        return
    user = update.effective_user
    guess = update.message.text.strip().lower()
    correct = context.user_data["answer"]
    if guess == correct:
        c.execute("UPDATE players SET xp = xp + 10 WHERE user_id=?", (user.id,))
        conn.commit()
        c.execute("SELECT xp, level FROM players WHERE user_id=?", (user.id,))
        xp, level = c.fetchone()
        new_level = xp // 50 + 1
        if new_level > level:
            c.execute("UPDATE players SET level=? WHERE user_id=?", (new_level, user.id))
            conn.commit()
            await update.message.reply_text(f"✅ Correct! +10 XP\n🌟 LEVEL UP! You're now level {new_level}!")
        else:
            await update.message.reply_text(f"✅ Correct! +10 XP (Total: {xp})")
    else:
        await update.message.reply_text(f"❌ Nope! The answer was: {correct}")
del context.user_data["answer"]

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    c.execute("SELECT * FROM players WHERE user_id=?", (user.id,))
    row = c.fetchone()
    if row:
        await update.message.reply_text(f"📜 {row[1]}\nClass: {row[2]}\nXP: {row[3]} | Level: {row[4]}")
    else:
        await update.message.reply_text("Send /start first!")

async def change_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(cls, callback_data=cls.split()[-1].lower())] for cls in CLASSES]
    await update.message.reply_text("Choose new class:", reply_markup=InlineKeyboardMarkup(keyboard))

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(CommandHandler("puzzle", puzzle))
app.add_handler(CommandHandler("profile", profile))
app.add_handler(CommandHandler("class", change_class))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer_handler))
print("PI Saga bot is running...")
app.run_polling()
