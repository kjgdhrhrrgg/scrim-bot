import discord
from discord.ext import commands
from utils import db 
import logging

logger = logging.getLogger("scrim-bot")

class Moderator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("Moderator cog loaded.")

    @commands.slash_command(name = "reset", description = "Reset scrim list")
    @commands.has_permissions(administrator = True)
    async def reset(self, ctx: discord.ApplicationContext):
        db.reset()
        await ctx.respond("Scrim list has been resetted.", ephemeral = True)
    

    @commands.slash_command(name = "ac", description = "Admin signup for scrims")
    @commands.has_permissions(administrator = True)
    async def c(
        self,
        ctx: discord.ApplicationContext,
        team: discord.Option(str, choices = ["Gold", "Crystal", "Ruby", "Silver", "Mixed"]), # type: ignore
        hour: discord.Option(int, choices = list(range(24))), # type: ignore
        user: discord.Option(discord.Member, description = "Choose a member"), # type: ignore
        role: discord.Option(str, choices = ["main", "sub"]), # type: ignore
        ):
            user_id = str(user.id)
            try:
                db.can(team = team, hour = hour, user_id = user_id, role = role)
                await ctx.respond(
                    f"✅ {user.mention} signed up for {team} at {hour}:00 as {role}.",
                ephemeral = True,
                )
            except Exception as e:
                await ctx.respond(f"❌ Error: {e}", ephemeral = True)

    @commands.slash_command(name = "ad", description = "Admin drop of a scrim")
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
            db.drop(team, hour, user_id )
            await ctx.respond(
                f"{ctx.user.mention} dropped off at {hour}:00 for {team}.",
                ephemeral=True,
            )
        except Exception as e:
            await ctx.respond(f"Error: {e}", ephemeral=True)

    @commands.slash_command(name = "ada", description = "Admin drop of every signed up scrim")
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

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond("❌ You don't have permission to use this command.", ephemeral = True)

def setup(bot):
    logging.info("Loading Moderator cog.")
    bot.add_cog(Moderator(bot))