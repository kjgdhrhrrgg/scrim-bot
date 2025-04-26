import discord
from discord.ext import commands
from utils import db

class ModDropAll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name = "ada", description = "Drop certain user of all signed up scrim")
    @commands.has_permissions(administrator = True)
    async def dropall(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Option(discord.Member, description = "Choose a member"), # type: ignore
    ):
        user_id = str(user.id)
        try:
            db.dropall(user_id)
            await ctx.respond(
                f"{user.mention} dropped off all scrims.",
                ephemeral = True,
            )
        except Exception as e:
            await ctx.respond(f"Error: {e}", ephemeral = True)

def setup(bot):
    bot.add_cog(ModDropAll(bot))