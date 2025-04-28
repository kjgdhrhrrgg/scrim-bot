import discord
from discord.ext import commands

class Presence(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name = "presence", description = "Change the bot's presence text (admin only)")
    @commands.has_permissions(administrator = True)
    async def presence(
        self,
        ctx: discord.ApplicationContext,
        presence_text: discord.Option(str, description = "New status text"),  # type: ignore
    ):
        await self.bot.change_presence(
            activity = discord.Game(name = presence_text),
            status = discord.Status.online,
        )
        await ctx.respond(f"✅ Presence updated to: `{presence_text}`", ephemeral = True)

def setup(bot):
    bot.add_cog(Presence(bot))