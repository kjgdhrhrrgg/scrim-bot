import discord
from discord.ext import commands
from utils.loader import reload_cogs
import logging

logger = logging.getLogger("scrim-bot")

class Reload(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name = "reload", description = "Reload all bot modules and sync commands (admin only)")
    @commands.has_permissions(administrator = True)
    async def reload(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral = True)

        success, failed, timings = reload_cogs(self.bot)

        try:
            await self.bot.sync_commands()
            sync_message = "✅ Synced slash commands."
        except Exception as e:
            sync_message = f"❌ Failed to sync commands: {e}"

        success_message = f"✅ Reloaded {len(success)} extensions."
        if failed:
            failed_message = "\n".join(f"❌ {ext}: {error}" for ext, error in failed)
            message = f"{success_message}\n\n{failed_message}\n\n{sync_message}"
        else:
            message = f"{success_message}\n\n{sync_message}"

        await ctx.respond(message, ephemeral = True)

        # Extra timing logs
        if timings:
            timings.sort(key=lambda x: x[1], reverse=True)
            logger.info("📈 Extension Reload Times:")
            for ext, ms in timings:
                logger.info(f"  {ext}: {ms:.2f} ms")

def setup(bot):
    bot.add_cog(Reload(bot))