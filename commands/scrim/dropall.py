import discord
from discord.ext import commands
from utils import db

class DropAll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name = "da", description = "Drop of every signed up scrim")
    async def dropall(
        self,
        ctx: discord.ApplicationContext,
    ):
        user_id = str(ctx.author.id)
        try:
            db.dropall(user_id)
            await ctx.respond(
                f"{ctx.author.mention} dropped off all scrims.",
                ephemeral = True,
            )
        except Exception as e:
            await ctx.respond(f"Error: {e}", ephemeral = True)

def setup(bot):
    bot.add_cog(DropAll(bot))