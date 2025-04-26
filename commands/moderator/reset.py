import discord
from discord.ext import commands
from utils import db

class ModReset(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name = "reset", description = "Reset scrim list")
    @commands.has_permissions(administrator = True)
    async def reset(self, ctx: discord.ApplicationContext):
        db.reset()
        await ctx.respond("Scrim list has been resetted.", ephemeral = True)

def setup(bot):
    bot.add_cog(ModReset(bot))