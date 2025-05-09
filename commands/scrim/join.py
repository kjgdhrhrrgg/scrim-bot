import discord
from discord.ext import commands
from discord.ui import View, Select, Button
from utils.db import can

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
        self.team_select.update_options()
        self.hour_select.update_options()
        self.role_select.update_options()

        embed = discord.Embed(
            title = "Scrim Sign Up",
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

        self.submit_button.disabled = not self.all_selected()

        await interaction.response.edit_message(embed = embed, view = self)

    class TeamSelect(Select):
        def __init__(self, view: View):
            self.view_ref = view
            options = [discord.SelectOption(label = label) for label in ["Gold", "Crystal", "Ruby", "Silver", "Mixed"]]
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
            options = [discord.SelectOption(label = str(h)) for h in reversed(range(24))]
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
                discord.SelectOption(label = "Main"),
                discord.SelectOption(label = "Sub"),
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
            skipped = set()
            success = set()
            for team in self.view_ref.selected_teams:
                for hour in self.view_ref.selected_hours:
                    try:
                        can(team = team, hour = int(hour), user_id = str(interaction.user.id), role = self.view_ref.selected_role.lower())
                        success.add(int(hour))
                    except Exception as e:
                        skipped.add(int(hour))

            embed = discord.Embed(
                title = "Signup Summary",
                color = discord.Color.green(),
            )
            if success:
                sorted_hours = sorted(success)
                embed.add_field(
                    name="✅ Signup Successful",
                    value=(
                        f"You successfully signed up as **{self.view_ref.selected_role}** "
                        f"for the following teams: **{', '.join(self.view_ref.selected_teams)}**\n\n" +
                        "\n".join(f"{hour}:00" for hour in sorted_hours)
                    ),
                    inline=False,
                )
            if skipped:
                embed.add_field(
                    name="⚠️ Already Signed Up",
                    value=(
                        "You are already signed up for a scrim at these times:\n" +
                        "\n".join(f"{hour}:00" for hour in sorted(skipped))
                    ),
                    inline=False,
        )
            await interaction.response.edit_message(embed = embed, view = None)

class Join(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name = "join", description = "Sign yourself up for multiple scrims.")
    async def join(self, ctx: discord.ApplicationContext):
        view = JoinView()
        embed = discord.Embed(
            title = "Scrim Signup",
            description = "Please select your options below. Then click Submit when ready.",
            color = discord.Color.blurple(),
        )
        await ctx.respond(embed = embed, view = view, ephemeral = True)

def setup(bot):
    bot.add_cog(Join(bot))
