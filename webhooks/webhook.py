import discord
import aiohttp
import asyncio
import os
import json
from datetime import datetime
from utils.db import get_list
from dotenv import load_dotenv

# Load environment
load_dotenv()
SCRIM_WEBHOOK_URL = os.getenv("SCRIM_WEBHOOK_URL")

# Path to save message ID
MESSAGE_ID_FILE = "data/webhook/message_id.txt"

# Make sure directory exists
os.makedirs(os.path.dirname(MESSAGE_ID_FILE), exist_ok=True)

def save_message_id(message_id):
    with open(MESSAGE_ID_FILE, "w") as f:
        f.write(str(message_id))

def load_message_id():
    try:
        with open(MESSAGE_ID_FILE, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None

async def format_signups():
    data = get_list()
    if not data:
        timestamp = int(datetime.now().timestamp())
        return f"No scrim signups yet.\n\nLast updated: <t:{timestamp}>"

    grouped = {}
    for row in data:
        key = (row["team"], row["hour"])
        if key not in grouped:
            grouped[key] = {"main": [], "sub": []}
        try:
            user_ids = json.loads(row["user_ids"]) if isinstance(row["user_ids"], str) else row["user_ids"]
            grouped[key][row["role"]] = user_ids
        except Exception:
            grouped[key][row["role"]] = []

    lines = []
    for (team, hour), roles in sorted(grouped.items()):
        main_ids = roles.get("main", [])
        sub_ids = roles.get("sub", [])
        main_list = ", ".join(f"<@{uid}>" for uid in main_ids) if main_ids else "—"
        sub_list = ", ".join(f"<@{uid}>" for uid in sub_ids) if sub_ids else "—"
        main_count = len(main_ids)
        lines.append(f"**{team}** {hour}:00 ({main_count}/6): {main_list} | Sub: {sub_list}")

    timestamp = int(datetime.now().timestamp())
    return "\n".join(lines) + f"\n\nLast updated: <t:{timestamp}>"

async def refresh_webhook():
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(SCRIM_WEBHOOK_URL, session = session)

        content = await format_signups()

        message_id = load_message_id()
        try:
            if message_id:
                try:
                    message = await webhook.fetch_message(message_id)
                    await message.edit(content=content)
                except discord.NotFound:
                    msg = await webhook.send(content, wait=True)
                    save_message_id(msg.id)
            else:
                msg = await webhook.send(content, wait=True)
                save_message_id(msg.id)
        except Exception as e:
            print(f"[Webhook Error] {e}")

async def webhook_updater(bot):
    await bot.wait_until_ready()
    while not bot.is_closed():
        bot.loop.create_task(refresh_webhook())  
        await asyncio.sleep(15)  