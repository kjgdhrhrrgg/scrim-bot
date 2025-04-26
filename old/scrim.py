import discord
from discord.ext import commands
from utils import db
import logging

logger = logging.getLogger("scrim-bot")

class Scrim(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("Scrim cog loaded.")

    

    @commands.slash_command(name = "d", description = "Drop of a scrim")
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
    logger.info("Loading Scrim cog.")
    bot.add_cog(Scrim(bot))
