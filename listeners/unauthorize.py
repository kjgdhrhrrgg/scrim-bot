import discord
from discord.ext import commands

class Unauthorized(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            # Only show error if the command comes from the moderator group
            if ctx.command.cog_name == "moderator":
                await ctx.respond("You don't have permission to use this moderator command.", ephemeral=True)

def setup(bot):
    bot.add_cog(Unauthorized(bot))
