import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from utils.db import init_db
from webhooks.webhook import webhook_updater  

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("scrim-bot")

# Load environment
load_dotenv()
TOKEN = os.getenv("KJ_ID")

# Set up bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.guild_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize DB
init_db()

# Load cogs
for folder in ["commands", "listeners"]:
    for root, dirs, files in os.walk(folder):
        for filename in files:
            if filename.endswith(".py") and not filename.startswith("_"):
                extension = root.replace("/", ".").replace("\\", ".") + "." + filename[:-3]
                try:
                    bot.load_extension(extension)
                    logger.info(f"✅ Loaded extension: {extension}")
                except Exception as e:
                    logger.error(f"❌ Failed to load extension {extension}: {e}")

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} ({bot.user.id})")
    await bot.change_presence(activity=discord.Game(name="Scrim Signups"))
    await bot.sync_commands()
    logger.info("✅ Synced commands")
    logger.info("✅ Starting webhook updater...")
    bot.loop.create_task(webhook_updater(bot))

# Start bot
bot.run(TOKEN)