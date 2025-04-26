import discord
from discord.ext import commands
from utils import db


class Drop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name = "d", description = "Remove yourself of a scrim")
    async def drop(
        self,
        ctx: discord.ApplicationContext,
        team: discord.Option(str, choices = ["Gold", "Crystal", "Ruby", "Silver", "Mixed"]), # type: ignore
        hour: discord.Option(int, choices = list(range(24))), # type: ignore
    ):
        user_id = str(ctx.author.id)
        try:
            db.drop(team, hour, user_id, )
            await ctx.respond(
                f"{ctx.author.mention} dropped off at {hour}:00 for {team}.",
                ephemeral=True,
            )
        except Exception as e:
            await ctx.respond(f"Error: {e}", ephemeral = True)

def setup(bot):
    bot.add_cog(Drop(bot))