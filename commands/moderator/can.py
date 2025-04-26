import discord 
from discord.ext import commands
from utils import db

class ModCan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name = "ac", description = "Sign up certain user for a scrim")
    @commands.has_permissions(administrator = True)
    async def c(
        self,
        ctx: discord.ApplicationContext,
        team: discord.Option(str, choices = ["Gold", "Crystal", "Ruby", "Silver", "Mixed"]), # type: ignore
        hour: discord.Option(int, choices = list(reversed(range(24)))), # type: ignore
        user: discord.Option(discord.Member, description = "Choose a member"), # type: ignore
        role: discord.Option(str, choices = ["main", "sub"]), # type: ignore
    ):
        user_id = str(user.id)
        try:
            db.can(team = team, hour = hour, user_id = user_id, role=role)
            await ctx.respond(
                f"✅ {ctx.author.mention} signed up for {team} at {hour}:00 as {role}.",
                ephemeral = True,
            )
        except Exception as e:
            await ctx.respond(f"❌ Error: {e}", ephemeral = True)

def setup(bot):
    bot.add_cog(ModCan(bot)) 
