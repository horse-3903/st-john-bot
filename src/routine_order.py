import discord
from discord import Interaction
from discord.ext.commands.context import Context

from datetime import datetime, timezone
import pytz
import parsedatetime

import asyncio

cal = parsedatetime.Calendar()

class CustomSelector(discord.ui.Select):
        def __init__(self, group_name: str, options: list, min_val: int, max_val: int, choice_name:str = None, select_placeholder: str = None, custom_input_placeholder: str = None):
            super().__init__(
                placeholder = select_placeholder,
                options = [discord.SelectOption(label=l, description=d) for l, d in options],
                min_values = min_val,
                max_values = max_val
            )
            self.group_name = group_name
            self.res = []
            self.choice_name = f" {choice_name} " if choice_name else " "
            self.custom_input_placeholder = custom_input_placeholder
            
        async def callback(self, interaction: Interaction):
            self.res = self.values

            if "Other" in self.values: 
                self.res.remove("Other")
                group_custom_modal = discord.ui.Modal(title=f"Routine Order {self.group_name}{self.choice_name}Information")
                group_custom_modal.add_item(
                    discord.ui.TextInput(
                        label=f"Input the custom{self.choice_name}option name",
                        placeholder=self.custom_input_placeholder,
                        required=True,
                    )
                )

                group_custom_modal.add_item(
                    discord.ui.TextInput(
                        label=f"Input the custom{self.choice_name}option name",
                        placeholder=self.custom_input_placeholder,
                        required=False,
                    )
                )

                async def group_custom_modal_callback(interaction2: discord.Interaction):
                    print(group_custom_modal.children)
                    custom = [" ".join([v.capitalize() if v != v.upper() else v for v in c.value.split(" ")]) for c in group_custom_modal.children]
                    self.res += custom
                    self.res = list(filter(lambda v: bool(v), self.res))
                    
                    await interaction2.response.defer()

                group_custom_modal.on_submit = group_custom_modal_callback
                await interaction.response.send_modal(group_custom_modal)
            else:
                await interaction.response.defer()
            self.res = sorted(self.res)
        
async def config_date(ctx: Context) -> dict: 
    date_view = discord.ui.View()
    date_button = discord.ui.Button(
        style = discord.ButtonStyle.secondary,
        label = "Set dates and times for event"
    )

    dates = {"reporting_dt" : None, "dismissal_dt" : None, "reminder_dt" : None}

    async def date_button_callback(interaction: Interaction):
        date_modal = discord.ui.Modal(title="Routine Order Date Information")
        date_modal.add_item(
            discord.ui.TextInput(
                label="Input the reporting day/date and time in 24-hour format", 
                required=(not dates["reporting_dt"]),
                placeholder=("Eg. Friday at 1530" if (not dates["reporting_dt"]) else f"Current: {dates['reporting_dt']}"),
            )
        )
        date_modal.add_item(
            discord.ui.TextInput(
                label="Input the dismissal date and time for event",
                required=(not dates["dismissal_dt"]),
                placeholder=("Eg. Friday at 1800" if (not dates["dismissal_dt"]) else f"Current: {dates['dismissal_dt']}"),
            )
        )
        date_modal.add_item(
            discord.ui.TextInput(
                label="Input the reminder date and time for event",
                required=(not dates["reminder_dt"]),
                placeholder=("Eg. Today at 2230" if (not dates["reminder_dt"]) else f"Current: {dates['reminder_dt']}"),
            )
        )

        async def date_modal_callback(interaction2: Interaction):
            dates["reporting_dt"] = cal.parseDT(date_modal.children[0].value, tzinfo=pytz.timezone("Asia/Singapore"))[0].strftime('%m/%d/%Y, %H:%M:%S')
            dates["dismissal_dt"] = cal.parseDT(date_modal.children[1].value, tzinfo=pytz.timezone("Asia/Singapore"))[0].strftime('%m/%d/%Y, %H:%M:%S')
            dates["reminder_dt"] = cal.parseDT(date_modal.children[2].value, tzinfo=pytz.timezone("Asia/Singapore"))[0].strftime('%m/%d/%Y, %H:%M:%S')

            date_check = "Dates and Times for event set to : "
            for s in ["Reporting", "Dismissal", "Reminder"]: 
                date_check += "\n"
                date_check += s + " " + "Time : "
                date_check += f"`{dates[s.lower() + '_dt']}`"
            
            await interaction2.response.send_message(content=date_check)

        date_modal.on_submit = date_modal_callback
        await interaction.response.send_modal(date_modal)

    date_button.callback = date_button_callback
    date_view.add_item(item=date_button)

    await ctx.send(view=date_view)
    return dates

async def config_groups(ctx: Context) -> list:
    groups_view = discord.ui.View()
    groups_options = [("Platoon 1", None), ("Platoon 2", None), ("Platoon 3", None), ("Other", "Make a custom group")]    
    groups_select = CustomSelector("Groups", groups_options, 2, 4, None, "Choose the groups going for this event", "(Eg. SBNDP)")
    
    groups_button = discord.ui.Button(
        style=discord.ButtonStyle.secondary,
        label="Set groups for the event"
    )

    input_event = asyncio.Event()
    groups = []

    async def groups_button_callback(interaction: Interaction):
        nonlocal groups

        if not groups_select.res:
            interaction.response.send_message("Please set the values of the groups for the event", ephemeral=True)
        else:
            groups = groups_select.res
            await interaction.response.send_message(f"Groups set to : \n`{', '.join(groups)}`")
            input_event.set()
    
    groups_button.callback = groups_button_callback
    groups_view.add_item(groups_select)
    groups_view.add_item(groups_button)

    await ctx.send(view=groups_view)

    await input_event.wait()
    return groups

async def config_attire(ctx: Context, info: dict = {"groups" : ["Platoon 1", "Platoon 2", "Platoon 3"]}) -> dict:
    attire_view = discord.ui.View()
    attire_options = [("PT Kit with Black Socks", None), ("FBU", None), ("Training Order", None), ("Drill Order", None), ("Other", "Make a custom attire")]
    attire_select = [CustomSelector(g, attire_options, 1, 1, "Attire", f"Choose the attire for {g} for this event", "(Eg. Half Uniform)") for g in info["groups"]]
    
    attire_button = discord.ui.Button(
        style = discord.ButtonStyle.secondary,
        label = "Set attire of all groups for this event"
    )

    input_event = asyncio.Event()
    attire = {}
    
    async def attire_button_callback(interaction: Interaction):
        nonlocal attire

        attire = {s.group_name.lower().replace(" ","")+"_attire": s.res for s in attire_select}

        attire_check = "Attire set to :"
        for k, v in attire.items():
            label = k.capitalize().replace("_attire", "")
            if label[-1].isnumeric():
                label = label[:-1] + " " + label[-1]
            attire_check += "\n"
            attire_check += label + " : " + f"`{v}`"

        await interaction.response.send_message(attire_check)
        input_event.set()
    
    attire_button.callback = attire_button_callback
    for s in attire_select:
        attire_view.add_item(s)
    attire_view.add_item(attire_button)

    await ctx.send(view=attire_view)

    await input_event.wait()
    return attire