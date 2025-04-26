import discord
from discord.ext import commands
import os

class Reload(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name = "reload", description = "Reload all bot modules and sync commands (admin only)")
    @commands.has_permissions(administrator = True)
    async def reload(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral = True)

        success = []
        failed = []

        # Unload and reload all extensions
        for folder in ["commands", "listeners"]:
            for root, dirs, files in os.walk(folder):
                for filename in files:
                    if filename.endswith(".py") and not filename.startswith("_"):
                        extension = root.replace("/", ".").replace("\\", ".") + "." + filename[:-3]
                        try:
                            self.bot.unload_extension(extension)
                            self.bot.load_extension(extension)
                            success.append(extension)
                        except Exception as e:
                            failed.append((extension, str(e)))

        # Try to sync commands
        try:
            await self.bot.sync_commands()
            sync_message = "✅ Synced slash commands. You may need to wait ~10 seconds for changes to apply."
        except Exception as e:
            sync_message = f"❌ Failed to sync commands: {e}"

        # Build the final message
        success_message = f"✅ Reloaded {len(success)} extensions."
        if failed:
            failed_message = "\n".join(f"❌ {ext}: {error}" for ext, error in failed)
            message = f"{success_message}\n\n{failed_message}\n\n{sync_message}"
        else:
            message = f"{success_message}\n\n{sync_message}"

        await ctx.respond(message, ephemeral = True)

def setup(bot):
    bot.add_cog(Reload(bot))