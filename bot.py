import json, random, os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ["YOUR_BOT_TOKEN"]
GROUP_ID = -1001234567890  # replace

XP_PER_CORRECT = 30
LEVEL_XP = {1: 0, 2: 100, 3: 250, 4: 500, 5: 800, 6: 1200}
CLASSES = ["Warrior", "Mage", "Rogue"]

RIDDLES = [
    ("What has keys but can't open locks?", "piano"),
    ("What gets wetter the more it dries?", "towel"),
    ("I follow you all day but disappear at night.", "shadow"),
]

def load():
    try:
        with open("players.json") as f: return json.load(f)
    except: return {}

def save(d):
    with open("players.json", "w") as f: json.dump(d, f, indent=2)

async def start(update: Update, ctx):
    u = update.effective_user
    p = load()
    uid = str(u.id)
    if uid in p:
        await update.message.reply_text("You already have an avatar.")
        return
    p[uid] = {"name": u.full_name, "class": random.choice(CLASSES), "level": 1, "xp": 0}
    save(p)
    await update.message.reply_text(f"⚔️ {u.full_name} | {p[uid]['class']} | Level 1")

async def puzzle(update: Update, ctx):
    q, a = random.choice(RIDDLES)
    ctx.chat_data["answer"] = a
    await update.message.reply_text(f"🧩 {q}")

async def check(update: Update, ctx):
    if update.message.chat_id != GROUP_ID: return
    ans = ctx.chat_data.get("answer")
    if not ans: return
    if update.message.text.strip().lower() != ans.lower(): return
    p = load()
    uid = str(update.effective_user.id)
    if uid not in p: return
    p[uid]["xp"] += XP_PER_CORRECT
    for lvl, need in sorted(LEVEL_XP.items(), reverse=True):
        if p[uid]["xp"] >= need and p[uid]["level"] < lvl:
            p[uid]["level"] = lvl
            await update.message.reply_text(f"🎉 Level up! {p[uid]['name']} → Level {lvl}")
            break
    save(p)
    await update.message.reply_text(f"+{XP_PER_CORRECT} XP")
    ctx.chat_data.pop("answer", None)

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("puzzle", puzzle))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Chat(GROUP_ID), check))

from flask import Flask
from threading import Thread
import time

app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot is alive"

def run_web():
    app_web.run(host='0.0.0.0', port=8080)

t = Thread(target=run_web)
t.start()

app.run_polling()
