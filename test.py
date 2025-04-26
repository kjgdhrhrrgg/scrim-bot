import discord
from discord.ext import commands
from discord.ui import Select, View
import os
from dotenv import load_dotenv
import logging


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    logging.info(f"Bot is online as {bot.user} (ID: {bot.user.id})")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    logging.info(f"Message from {message.author}: {message.content}")
    await bot.process_commands(message)


@bot.event
async def on_command(ctx):
    logging.info(f"Command used: {ctx.command} by {ctx.author}")


# Step 1: Team selection
class TeamSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Gold"),
            discord.SelectOption(label="Crystal"),
            discord.SelectOption(label="Ruby"),
            discord.SelectOption(label="Silver"),
            discord.SelectOption(label="Mixed"),
        ]
        super().__init__(
            placeholder="Choose your teams", min_values=1, max_values=5, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_teams = self.values
        await interaction.response.edit_message(
            content="✅ Teams selected. Now choose available hours:",
            view=HourView(self.view.selected_teams),
        )


class TeamView(View):
    def __init__(self):
        super().__init__()
        self.selected_teams = None
        self.add_item(TeamSelect())


# Step 2: Hour selection
class HourSelect(Select):
    def __init__(self):
        options = [discord.SelectOption(label=str(h), value=str(h)) for h in range(24)]
        super().__init__(
            placeholder="Choose your available hours (0-23)",
            min_values=1,
            max_values=24,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_hours = self.values
        await interaction.response.edit_message(
            content="✅ Hours selected. Now choose your role:",
            view=RoleView(self.view.selected_teams, self.view.selected_hours),
        )


class HourView(View):
    def __init__(self, selected_teams):
        super().__init__()
        self.selected_teams = selected_teams
        self.selected_hours = None
        self.add_item(HourSelect())


# Step 3: Role selection
class RoleSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Main"),
            discord.SelectOption(label="Sub"),
        ]
        super().__init__(
            placeholder="Choose your role", min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected_role = self.values[0]
        selected_teams = self.view.selected_teams
        selected_hours = self.view.selected_hours

        response = (
            f"✅ All selections complete!\n"
            f"**Teams:** {', '.join(selected_teams)}\n"
            f"**Hours:** {', '.join(selected_hours)}\n"
            f"**Role:** {selected_role}"
        )

        await interaction.response.edit_message(content=response, view=None)


class RoleView(View):
    def __init__(self, selected_teams, selected_hours):
        super().__init__()
        self.selected_teams = selected_teams
        self.selected_hours = selected_hours
        self.add_item(RoleSelect())


# Trigger command
@bot.command()
async def register(ctx):
    """Starts the interactive registration process."""
    await ctx.send("Select your teams:", view=TeamView())


load_dotenv()
TOKEN = os.getenv("KJ_ID")
bot.run(TOKEN)
