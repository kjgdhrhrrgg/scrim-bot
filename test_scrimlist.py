import discord
import asyncio
import json
import os
from utils.db import get_list
from dotenv import load_dotenv

load_dotenv()
SCRIM_WEBHOOK_URL = os.getenv("SCRIM_WEBHOOK_URL")
WEBHOOK_URL = os.getenv("SCRIM_WEBHOOK_URL")

last_payload = None
message_id = None

async def format_signups():
    data = get_list()
    print(f"[WEBHOOK] Fetched data: {data}")  # Debug log
    if not data:
        return "No scrim signups yet."

    # Structure: { (team, hour): {"main": [...], "sub": [...]} }
    grouped = {}
    for row in data:
        key = (row["team"], row["hour"])
        if key not in grouped:
            grouped[key] = {"main": [], "sub": []}
        grouped[key][row["role"]] = json.loads(row["user_ids"])

    lines = []
    for (team, hour), roles in sorted(grouped.items()):
        main_ids = roles.get("main", [])
        sub_ids = roles.get("sub", [])
        main_list = ", ".join(f"<@{uid}>" for uid in main_ids) if main_ids else "—"
        sub_list = ", ".join(f"<@{uid}>" for uid in sub_ids) if sub_ids else "—"
        main_count = len(main_ids)
        max_size = 6  # Optional: query from DB if needed
        lines.append(f"**{team}** {hour}:00 ({main_count}/6): {main_list} | Sub: {sub_list}")

    message = "\n".join(lines)
    print(f"[WEBHOOK] Formatted message: {message}")  # Debug log

    return message


print(format_signups())

async def webhook_updater(bot):
    global last_payload, message_id
    await asyncio.sleep(5)  # Wait a bit for bot startup

    session = bot.http._HTTPClient__session
    webhook = discord.Webhook.from_url(WEBHOOK_URL, session = session)

    while True:
        try:
            content = await format_signups()
            print(f"[WEBHOOK] Formatted content: {content}")  # Debug log
            if content != last_payload:
                last_payload = content
                print(f"[WEBHOOK] Sending new payload: {content}") # Debug log
                if message_id:
                    try:
                        message = await webhook.fetch_message(message_id)
                        await message.edit(content=content)
                    except discord.NotFound:
                        msg = webhook.send(content, wait=True)
                        message_id = msg.id
                else:
                    msg = webhook.send(content, wait=True)
                    message_id = msg.id
        except Exception as e:
            print(f"[WEBHOOK ERROR] {e}")

        await asyncio.sleep(60)
