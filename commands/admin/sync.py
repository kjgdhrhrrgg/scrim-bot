import discord
from discord.ext import commands

class Sync(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name = "sync", description = "Sync application commands (admin only)")
    @commands.has_permissions(administrator = True)
    async def sync(self, ctx: discord.ApplicationContext, scope: discord.Option(str, choices=["global", "guild"])): # type: ignore
        await ctx.defer(ephemeral = True)

        try:
            if scope == "guild":
                synced = await self.bot.sync_commands(guild = ctx.guild)
                message = f"✅ Synced {len(synced)} commands to **this guild** ({ctx.guild.name})."
            else:
                synced = await self.bot.sync_commands()
                message = f"✅ Synced {len(synced)} commands **globally** (may take up to 1 hour to update)."

            await ctx.respond(message, ephemeral = True)
        except Exception as e:
            await ctx.respond(f"❌ Sync failed: {e}", ephemeral = True)

def setup(bot):
    bot.add_cog(Sync(bot))