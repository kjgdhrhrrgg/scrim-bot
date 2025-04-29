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

# Path to save message IDs
MESSAGE_ID_FILE = "data/webhook/message_ids.json"

# Make sure directory exists
os.makedirs(os.path.dirname(MESSAGE_ID_FILE), exist_ok=True)

def save_message_ids(ids):
    with open(MESSAGE_ID_FILE, "w") as f:
        json.dump(ids, f)

def load_message_ids():
    try:
        with open(MESSAGE_ID_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        return []

async def format_signups():
    signups = get_list("signups")
    ready = get_list("ready")
    timestamp = int(datetime.now().timestamp())
    team_order = ["Gold", "Crystal", "Ruby", "Silver", "Mixed"]

    content_blocks = []

    # --- Scrim Signups ---
    content_blocks.append("# Scrim Signups")

    if not signups:
        content_blocks.append("No signups today.")
    else:
        # --- Grouped by hour ---
        grouped = {}
        for row in signups:
            key = (row["hour"], row["team"])
            if key not in grouped:
                grouped[key] = {"main": [], "sub": []}
            grouped[key][row["role"]] = row["user_ids"]

        sorted_keys = sorted(grouped.keys(), key=lambda x: (x[0], team_order.index(x[1]) if x[1] in team_order else 999))

        hour_content = []
        current_hour = None
        for hour, team in sorted_keys:
            roles = grouped[(hour, team)]
            if hour != current_hour:
                if current_hour is not None:
                    hour_content.append("")
                hour_content.append(f"## {hour}:00:")
                current_hour = hour

            main_ids = roles.get("main", [])
            sub_ids = roles.get("sub", [])
            main_list = ", ".join(f"<@{uid}>" for uid in main_ids) if main_ids else "—"
            sub_list = ", ".join(f"<@{uid}>" for uid in sub_ids) if sub_ids else "—"
            count = len(main_ids)
            hour_content.append(f"**{team}** ({count}/6): {main_list} | Sub: {sub_list}")

        content_blocks.append("\n".join(hour_content))

    # --- Full Lu's ---
    ready_grouped = {}
    for row in ready:
        key = (row["hour"], row["team"])
        ready_grouped[key] = row["user_ids"]

    if ready_grouped:
        full_lus_content = ["\n# Full Lu's:"]
        for hour in sorted(set(k[0] for k in ready_grouped.keys())):
            full_lus_content.append(f"## {hour}:00:")
            for team in team_order:
                key = (hour, team)
                if key in ready_grouped:
                    ids = ready_grouped[key]
                    mentions = ", ".join(f"<@{uid}>" for uid in ids)
                    full_lus_content.append(f"**{team}**: {mentions}")
            full_lus_content.append("")

        content_blocks.append("\n".join(full_lus_content))

    content_blocks.append(f"Last updated: <t:{timestamp}>")
    return "\n".join(content_blocks)

async def refresh_webhook():
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(SCRIM_WEBHOOK_URL, session=session)

        content = await format_signups()

        message_ids = load_message_ids()

        # Split if too long
        messages = []
        while content:
            chunk = content[:2000]
            last_split = chunk.rfind("\n")
            if last_split == -1:
                last_split = 2000
            messages.append(content[:last_split])
            content = content[last_split:].lstrip()

        try:
            # Edit existing or send new
            new_ids = []
            for i, chunk in enumerate(messages):
                if i < len(message_ids):
                    try:
                        msg = await webhook.fetch_message(message_ids[i])
                        await msg.edit(content=chunk)
                        new_ids.append(msg.id)
                    except discord.NotFound:
                        msg = await webhook.send(chunk, wait=True)
                        new_ids.append(msg.id)
                else:
                    msg = await webhook.send(chunk, wait=True)
                    new_ids.append(msg.id)

            # Clean up old extra messages
            for msg_id in message_ids[len(messages):]:
                try:
                    msg = await webhook.fetch_message(msg_id)
                    await msg.delete()
                except discord.NotFound:
                    continue

            save_message_ids(new_ids)
        except Exception as e:
            print(f"[Webhook Error] {e}")

async def webhook_updater(bot):
    await bot.wait_until_ready()
    while not bot.is_closed():
        bot.loop.create_task(refresh_webhook())
        await asyncio.sleep(15)
