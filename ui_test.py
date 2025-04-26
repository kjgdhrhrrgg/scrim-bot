import discord
from discord.ext import commands
from discord.ui import View, Select, Button
import logging
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


# ========== TEAM SELECT ==========
class TeamSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=label)
            for label in ["Gold", "Crystal", "Ruby", "Silver", "Mixed"]
        ]
        super().__init__(
            placeholder="Choose your teams", min_values=1, max_values=5, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        view: TeamView = self.view
        view.selected_teams = self.values
        embed = discord.Embed(
            title="Teams Selected",
            description=f"✅ You selected the following teams: {', '.join(self.values)}",
            color=discord.Color.green(),
        )
        embed.add_field(
            name="Next Step",
            value="Click `Confirm` to continue or `Go Back` to modify your selection.",
        )
        await interaction.response.edit_message(
            embed=embed, view=self.view.with_confirmation_buttons()
        )


class TeamView(View):
    def __init__(self):
        super().__init__()
        self.selected_teams = []
        self.add_item(TeamSelect())  # Automatically sets the view

    def with_confirmation_buttons(self):
        return ConfirmButtons(self, HourView)


# ========== HOUR SELECT ==========
class HourSelect(Select):
    def __init__(self):
        options = [discord.SelectOption(label=str(h)) for h in range(24)]
        super().__init__(
            placeholder="Choose available hours (0–23)",
            min_values=1,
            max_values=24,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        view: HourView = self.view
        view.selected_hours = self.values
        embed = discord.Embed(
            title="Hours Selected",
            description=f"✅ You selected the following hours: {', '.join(self.values)}",
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="Next Step",
            value="Click `Confirm` to continue or `Go Back` to modify your selection.",
        )
        await interaction.response.edit_message(
            embed=embed, view=self.view.with_confirmation_buttons()
        )


class HourView(View):
    def __init__(self, prev_view):
        super().__init__()
        self.prev_view = prev_view
        self.selected_teams = prev_view.selected_teams
        self.selected_hours = []
        self.add_item(HourSelect())  # Automatically sets the view

    def with_confirmation_buttons(self):
        return ConfirmButtons(self, RoleView)


# ========== ROLE SELECT ==========
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
        view: RoleView = self.view
        view.selected_role = self.values[0]
        embed = discord.Embed(
            title="Role Selected",
            description=f"✅ You selected the role: {self.values[0]}",
            color=discord.Color.purple(),
        )
        embed.add_field(
            name="Next Step",
            value="Click `Confirm` to finish or `Go Back` to modify your selection.",
        )
        await interaction.response.edit_message(
            embed=embed, view=self.view.with_confirmation_buttons()
        )


class RoleView(View):
    def __init__(self, prev_view):
        super().__init__()
        self.prev_view = prev_view
        self.selected_teams = prev_view.selected_teams
        self.selected_hours = prev_view.selected_hours
        self.selected_role = ""
        self.add_item(RoleSelect())  # Automatically sets the view

    def with_confirmation_buttons(self):
        return FinalConfirmationButtons(self)


# ========== BUTTONS ==========
class ConfirmButtons(View):
    def __init__(self, prev_view, next_view_class):
        super().__init__()
        self.prev_view = prev_view
        self.next_view_class = next_view_class

    @discord.ui.button(
        label="✅ Confirm",
        style=discord.ButtonStyle.success,
        custom_id="confirm_button",  # Unique custom ID
        emoji="✅",
    )
    async def confirm(self, button, interaction):
        await interaction.response.edit_message(
            content="Moving to the next step...",
            view=self.next_view_class(self.prev_view),
        )

    @discord.ui.button(
        label="🔙 Go Back",
        style=discord.ButtonStyle.danger,
        custom_id="go_back_button",  # Unique custom ID
        emoji="🔙",
    )
    async def go_back(self, button, interaction):
        await interaction.response.edit_message(
            content="Going back to the previous step...", view=self.prev_view
        )


# Final confirmation & summary
class FinalConfirmationButtons(View):
    def __init__(self, final_view):
        super().__init__()
        self.final_view = final_view

    @discord.ui.button(
        label="✅ Submit",
        style=discord.ButtonStyle.success,
        custom_id="submit_button",  # Unique custom ID
        emoji="✅",
    )
    async def submit(self, button, interaction):
        summary = (
            f"✅ **All selections complete!**\n"
            f"**Teams:** {', '.join(self.final_view.selected_teams)}\n"
            f"**Hours:** {', '.join(self.final_view.selected_hours)}\n"
            f"**Role:** {self.final_view.selected_role}"
        )
        logging.info(
            f"{interaction.user} registered: {summary.replace('✅ **All selections complete!**\n', '')}"
        )
        embed = discord.Embed(
            title="Registration Complete",
            description=summary,
            color=discord.Color.green(),
        )
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(
        label="🔙 Go Back",
        style=discord.ButtonStyle.danger,
        custom_id="go_back_final",  # Unique custom ID
        emoji="🔙",
    )
    async def go_back(self, button, interaction):
        await interaction.response.edit_message(
            content="Going back to Hour selection...", view=self.final_view.prev_view
        )


# ========== COMMAND ==========
@bot.command()
async def can(ctx):
    embed = discord.Embed(
        title="Step 1: Select your teams",
        description="Please select the teams you want to participate in. You can choose multiple teams (1–5).",
        color=discord.Color.blue(),
    )
    await ctx.send(embed=embed, view=TeamView())


@bot.event
async def on_ready():
    logging.info(f"Bot is online as {bot.user}")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)


load_dotenv()
TOKEN = os.getenv("KJ_ID")
bot.run(TOKEN)

