import discord
from discord.ext import commands
from utils import db


class ModDrop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name = "ad", description = "Remove certain user of a scrim")
    @commands.has_permissions(administrator = True)
    async def drop(
        self,
        ctx: discord.ApplicationContext,
        team: discord.Option(str, choices = ["Gold", "Crystal", "Ruby", "Silver", "Mixed"]), # type: ignore
        hour: discord.Option(int, choices = list(range(24))), # type: ignore
        user: discord.Option(discord.Member, description = "Choose a member"), # type: ignore
    ):
        user_id = str(user.id)
        try:
            db.drop(team, hour, user_id, )
            await ctx.respond(
                f"{user.mention} dropped off at {hour}:00 for {team}.",
                ephemeral=True,
            )
        except Exception as e:
            await ctx.respond(f"Error: {e}", ephemeral = True)

def setup(bot):
        bot.add_cog(ModDrop(bot))