import discord
from discord.ext import commands
from discord.ui import View, Select, Button
import logging

class JoinView(View):
    def __init__(self):
        super().__init__(timeout = 300)
        self.selected_teams = []
        self.selected_hours = []
        self.selected_role = None

        self.team_select = self.TeamSelect(self)
        self.hour_select = self.HourSelect(self)
        self.role_select = self.RoleSelect(self)
        self.submit_button = self.SubmitButton(self)

        self.add_item(self.team_select)
        self.add_item(self.hour_select)
        self.add_item(self.role_select)
        self.add_item(self.submit_button)

    def all_selected(self):
        return self.selected_teams and self.selected_hours and self.selected_role

    async def update_message(self, interaction: discord.Interaction):
        # Update the selected states visually
        self.team_select.update_options()
        self.hour_select.update_options()
        self.role_select.update_options()

        embed = discord.Embed(
            title = "Scrim Registration",
            description = "Please select your options below. Then click Submit when ready.",
            color = discord.Color.blurple(),
        )
        if self.selected_teams:
            embed.add_field(name = "Teams", value = ", ".join(self.selected_teams), inline = False)
        if self.selected_hours:
            sorted_hours = sorted(self.selected_hours, key = lambda x: int(x))
            embed.add_field(name = "Hours", value = ", ".join(sorted_hours), inline = False)
        if self.selected_role:
            embed.add_field(name = "Role", value = self.selected_role, inline = False)

        # Enable/Disable Submit
        self.submit_button.disabled = not self.all_selected()

        await interaction.response.edit_message(embed = embed, view = self)

    class TeamSelect(Select):
        def __init__(self, view: View):
            self.view_ref = view
            options = [discord.SelectOption(label=label) for label in ["Gold", "Crystal", "Ruby", "Silver", "Mixed"]]
            super().__init__(
                placeholder = "Select your teams",
                min_values = 1,
                max_values = 5,
                options = options,
                custom_id = "team_select",
            )

        def update_options(self):
            for option in self.options:
                option.default = option.label in self.view_ref.selected_teams

        async def callback(self, interaction: discord.Interaction):
            self.view_ref.selected_teams = self.values
            await self.view_ref.update_message(interaction)

    class HourSelect(Select):
        def __init__(self, view: View):
            self.view_ref = view
            options = [discord.SelectOption(label=str(h)) for h in reversed(range(24))]
            super().__init__(
                placeholder = "Select available hours (0–23)",
                min_values = 1,
                max_values = 24,
                options = options,
                custom_id = "hour_select",
            )

        def update_options(self):
            for option in self.options:
                option.default = option.label in self.view_ref.selected_hours

        async def callback(self, interaction: discord.Interaction):
            self.view_ref.selected_hours = self.values
            await self.view_ref.update_message(interaction)

    class RoleSelect(Select):
        def __init__(self, view: View):
            self.view_ref = view
            options = [
                discord.SelectOption(label="Main"),
                discord.SelectOption(label="Sub"),
            ]
            super().__init__(
                placeholder = "Select your role",
                min_values = 1,
                max_values = 1,
                options = options,
                custom_id = "role_select",
            )

        def update_options(self):
            for option in self.options:
                option.default = option.label == self.view_ref.selected_role

        async def callback(self, interaction: discord.Interaction):
            self.view_ref.selected_role = self.values[0]
            await self.view_ref.update_message(interaction)

    class SubmitButton(Button):
        def __init__(self, view: View):
            super().__init__(
                label = "✅ Submit",
                style = discord.ButtonStyle.success,
                custom_id = "submit_button",
                disabled = True,
            )
            self.view_ref = view

        async def callback(self, interaction: discord.Interaction):
            summary = (
                f"✅ **Registration Complete!**\n"
                f"**Teams:** {', '.join(self.view_ref.selected_teams)}\n"
                f"**Hours:** {', '.join(self.view_ref.selected_hours)}\n"
                f"**Role:** {self.view_ref.selected_role}"
            )
            logging.info(f"{interaction.user} registered: {summary.replace('✅ **Registration Complete!**\\n', '')}")

            embed = discord.Embed(
                title = "Registration Submitted",
                description = summary,
                color = discord.Color.green(),
            )
            await interaction.response.edit_message(embed = embed, view = None)

class Join(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name = "join", description = "Join multiple scrims.")
    async def join(self, ctx: discord.ApplicationContext):
        view = JoinView()
        embed = discord.Embed(
            title = "Scrim Registration",
            description = "Please select your options below. Then click Submit when ready.",
            color = discord.Color.blurple(),
        )
        await ctx.respond(embed = embed, view = view, ephemeral = True)  # <<< ephemeral = True

def setup(bot):
    bot.add_cog(Join(bot))