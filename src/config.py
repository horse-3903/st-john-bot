import discord
from discord import Interaction
from discord.ext.commands.context import Context

from datetime import datetime, timezone, timedelta
import pytz
import parsedatetime

import enchant

import asyncio

cal = parsedatetime.Calendar()
dictionary = enchant.Dict("en_US")

class CustomSelector(discord.ui.Select):
        def __init__(self, group_name: str, options: list, category:str = None, min_val: int = 1, max_val: int = 1, row:int = None, select_placeholder: str = None, custom_input_placeholder: str = None):
            super().__init__(
                placeholder = select_placeholder,
                options = [discord.SelectOption(label=l, description=d) for l, d in options],
                min_values = min_val,
                max_values = max_val,
                row=None
            )
            self.group_name = group_name
            self.res = []
            self.category = f" {category} " if category else " "
            self.custom_input_placeholder = custom_input_placeholder
            
        async def callback(self, interaction: Interaction):
            self.res = self.values

            if "Other" in self.values: 
                self.res.remove("Other")
                group_custom_modal = discord.ui.Modal(title=f"Routine Order {self.group_name}{self.category}Information")
                group_custom_modal.add_item(
                    discord.ui.TextInput(
                        label=f"Input the custom{self.category}option name",
                        placeholder=self.custom_input_placeholder,
                        required=True,
                    )
                )

                async def group_custom_modal_callback(interaction2: discord.Interaction):
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

    msg = f"**Select the dates of the Routine Order**"
    for k, v in dates.items():
        msg += "\n"
        msg += f"**{k[:-3].capitalize()} Time** is set to : `{v}`"

    async def date_button_callback(interaction: Interaction):
        date_modal = discord.ui.Modal(title="Routine Order Date Information")
        date_modal.add_item(
            discord.ui.TextInput(
                label="Input the reporting date and time for event", 
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

            msg = f"**Select the dates of the Routine Order**"
            for k, v in dates.items():
                msg += "\n"
                msg += f"**{k[:-3].capitalize()} Time** is set to : `{v}`"
            
            await msg_obj.edit(content=msg)
            
            await interaction2.response.defer()

        date_modal.on_submit = date_modal_callback
        await interaction.response.send_modal(date_modal)

    date_button.callback = date_button_callback
    date_view.add_item(item=date_button)

    msg_obj = await ctx.send(content=msg, view=date_view)
    
    return dates

async def config_groups(ctx: Context, info: dict = {"reporting_dt" : (datetime.now(pytz.timezone("Asia/Singapore")) + timedelta(days=1)).strftime('%m/%d/%Y, %H:%M:%S'), "dismissal_dt" : (datetime.now(pytz.timezone("Asia/Singapore")) + timedelta(days=1)).strftime('%m/%d/%Y, %H:%M:%S'), "reminder_dt" : datetime.now(pytz.timezone("Asia/Singapore")).strftime('%m/%d/%Y, %H:%M:%S')}) -> dict:
    groups_view = discord.ui.View()
    groups_options = [("Platoon 1", None), ("Platoon 2", None), ("Platoon 3", None), ("Platoon 4", None), ("Other", "Make a custom group")]    
    groups_select = CustomSelector(group_name="Groups", options=groups_options, category=None, min_val=2, max_val=5, select_placeholder="Choose the groups going", custom_input_placeholder="(Eg. SBNDP)")
    
    groups_button = discord.ui.Button(
        style=discord.ButtonStyle.secondary,
        label="Set groups for the event"
    )

    input_event = asyncio.Event()
    groups = []

    msg = f"**Select the groups involved in the Routine Order**"
    msg += f"\nGroups set to : `None`"

    async def groups_button_callback(interaction: Interaction):
        nonlocal groups

        if not groups_select.res:
            interaction.response.send_message("Please set the values of the groups for the event", ephemeral=True)
        else:
            groups = groups_select.res

            for i, g in enumerate(groups):
                label = g.split(" ")
                for s in range(len(label)):
                    if not dictionary.check(label[s]):
                        label[s] = label[s].upper()
                    else:
                        label[s] = label[s].capitalize()
                label = " ".join(label)
                groups[i] = label
            msg = f"**Select the groups involved in the Routine Order**"
            msg += f"\n**Groups** are set to : {', '.join([f'`{g}`' for g in groups])}"

            await msg_obj.edit(content=msg)
            await interaction.response.defer()
            input_event.set()
    
    groups_button.callback = groups_button_callback
    groups_view.add_item(groups_select)
    groups_view.add_item(groups_button)

    msg_obj = await ctx.send(content=msg, view=groups_view)

    await input_event.wait()
    return {"groups" : groups}

async def config_attire(ctx: Context, info: dict = {"reporting_dt" : (datetime.now(pytz.timezone("Asia/Singapore")) + timedelta(days=1)).strftime('%m/%d/%Y, %H:%M:%S'), "dismissal_dt" : (datetime.now(pytz.timezone("Asia/Singapore")) + timedelta(days=1)).strftime('%m/%d/%Y, %H:%M:%S'), "reminder_dt" : datetime.now(pytz.timezone("Asia/Singapore")).strftime('%m/%d/%Y, %H:%M:%S'), "groups" : ["Platoon 1", "Platoon 2", "Platoon 3", "Platoon 4"]}) -> dict:
    attire_view = discord.ui.View()
    attire_button_view = discord.ui.View()

    attire_options = [("PT Kit with Black Socks", None), ("FBU", None), ("Training Order", None), ("Drill Order", None), ("Other", "Make a custom attire")]
    default = attire_options[0][0] if datetime.strptime(info["reporting_dt"], '%m/%d/%Y, %H:%M:%S').weekday() == 2 else attire_options[1][0]

    attire_select = [CustomSelector(group_name=g, options=attire_options, category="Attire", select_placeholder=f"Choose the attire for {g}", custom_input_placeholder="(Eg. Half Uniform)") for g in info["groups"]]
    
    attire_button = discord.ui.Button(
        style = discord.ButtonStyle.secondary,
        label = "Set attires"
    )

    default_button = discord.ui.Button(
        style = discord.ButtonStyle.primary,
        label = "Set default attires"
    )

    input_event = asyncio.Event()
    attire = {g.lower().replace(" ","_")+"_attire": None for g in info["groups"]}

    msg = f"**Select the attire of the Routine Order**"
    for k, v in attire.items():
        label = k.replace('_attire', '').split("_")
        for s in range(len(label)):
            if not dictionary.check(label[s]):
                label[s] = label[s].upper()
            else:
                label[s] = label[s].capitalize()
        label = " ".join(label)

        msg += "\n"
        msg += f"**{label} Attire** is set to : `{v}`"
    
    async def attire_button_callback(interaction: Interaction):
        nonlocal attire

        if not attire:
            attire = {s.group_name.lower().replace(" ","_")+"_attire": s.res[0] for s in attire_select}
        else:
            for s in attire_select:
                if s.res:
                    attire[s.group_name.lower().replace(" ","_")+"_attire"] = s.res[0]

        msg = f"**Select the attire of the Routine Order**"
        for k, v in attire.items():
            label = k.replace('_attire', '').split("_")
            for s in range(len(label)):
                if not dictionary.check(label[s]):
                    label[s] = label[s].upper()
                else:
                    label[s] = label[s].capitalize()
            label = " ".join(label)
            
            msg += "\n"
            msg += f"**{label} Attire** is set to : `{v}`"

        await msg_obj.edit(content=msg)
        await interaction.response.defer()
        input_event.set()

    async def default_button_callback(interaction: Interaction):
        nonlocal attire

        attire = {s.group_name.lower().replace(" ","_")+"_attire": default for s in attire_select}

        msg = f"**Select the attire of the Routine Order**"
        for k, v in attire.items():
            label = k.replace('_attire', '').split("_")
            for s in range(len(label)):
                if not dictionary.check(label[s]):
                    label[s] = label[s].upper()
                else:
                    label[s] = label[s].capitalize()
            label = " ".join(label)
            
            msg += "\n"
            msg += f"**{label} Attire** is set to : `{v}`"

        await msg_obj.edit(content=msg)
        await interaction.response.defer()
        input_event.set()
    
    attire_button.callback = attire_button_callback
    default_button.callback = default_button_callback
    for s in attire_select:
        attire_view.add_item(s)
    attire_button_view.add_item(attire_button)
    attire_button_view.add_item(default_button)

    msg_obj = await ctx.send(content=msg, view=attire_view)
    await ctx.send(view=attire_button_view)

    await input_event.wait()
    return attire

async def config_venue(ctx: Context, info: dict = {"groups" : ["Platoon 1", "Platoon 2", "Platoon 3", "Platoon 4"]}) -> dict:
    venue_view = discord.ui.View()
    wet_venue_view = discord.ui.View()
    venue_button_view = discord.ui.View()

    venue_options = [("Amphitheatre", None), ("Other", "Make a custom venue")]
    default_venue = venue_options[0][0] # change
    wet_venue_options = [("Cadets' Room", None), ("Benches outside Cadets' Room", None), ("Benches beside Piano", None), ("Other", "Make a custom venue")]
    default_wet_venue = wet_venue_options[0][0] # change

    venue_select = [CustomSelector(group_name=g, options=venue_options, category="venue", row=0, select_placeholder=f"Choose the venue for {g}", custom_input_placeholder="(Eg. Amphitheatre)") for g in info["groups"]]
    wet_venue_select = [CustomSelector(group_name=g, options=wet_venue_options, category="venue", row=0, select_placeholder=f"Choose the wet weather venue for {g}", custom_input_placeholder="(Eg. Salt Centre)") for g in info["groups"]]
    
    venue_button = discord.ui.Button(
        style = discord.ButtonStyle.secondary,
        label = "Set venues and wet venues"
    )

    default_button = discord.ui.Button(
        style = discord.ButtonStyle.primary,
        label = "Set default reporting venues",
        row=1
    )

    wet_default_button = discord.ui.Button(
        style = discord.ButtonStyle.primary,
        label = "Set default wet weather venues",
        row=1
    )

    input_event = asyncio.Event()
    venue = {g.lower().replace(" ","_")+"_venue": None for g in info["groups"]}
    wet_venue = {g.lower().replace(" ","_")+"_wet_venue": None for g in info["groups"]}

    venue_msg = f"**Select the venue of the Routine Order**"
    for k, v in venue.items():
        label = k.replace('_venue', '').split("_")
        for s in range(len(label)):
            if not dictionary.check(label[s]):
                label[s] = label[s].upper()
            else:
                label[s] = label[s].capitalize()
        label = " ".join(label)
        
        venue_msg += "\n"
        venue_msg += f"**{label} Venue** is set to : `{v}`"

    wet_venue_msg = f"**Select the wet weather venue of the Routine Order**"
    for k, v in wet_venue.items():
        label = k.replace('_wet_venue', '').split("_")
        for s in range(len(label)):
            if not dictionary.check(label[s]):
                label[s] = label[s].upper()
            else:
                label[s] = label[s].capitalize()
        label = " ".join(label)
        
        wet_venue_msg += "\n"
        wet_venue_msg += f"**{label} Wet Weather Venue** is set to : `{v}`"
    
    async def venue_button_callback(interaction: Interaction):
        nonlocal venue, wet_venue

        venue = {s.group_name.lower().replace(" ","_")+"_venue": s.res for s in venue_select}
        wet_venue = {s.group_name.lower().replace(" ","_")+"_wet_venue": s.res for s in wet_venue_select}

        venue_check = "Venue set to :"
        for k, v in venue.items():
            label = k.capitalize().replace("_venue", "")
            if label[-1].isnumeric():
                label = label[:-1] + " " + label[-1]
            venue_check += "\n"
            venue_check += label + " : " + f"`{v}`"

        wet_venue_check = "Wet Weather Venue set to :"
        for k, v in wet_venue.items():
            label = k.capitalize().replace("_venue", "")
            if label[-1].isnumeric():
                label = label[:-1] + " " + label[-1]
            wet_venue_check += "\n"
            wet_venue_check += label + " : " + f"`{v}`"

        await interaction.response.send_message(venue_check + "\n" + wet_venue_check)
        input_event.set()

    async def default_button_callback(interaction: Interaction):
        nonlocal venue

        venue = {s.group_name.lower().replace(" ","_")+"_venue": default_venue for s in venue_select}

        venue_msg = f"**Select the venue of the Routine Order**"
        for k, v in venue.items():
            label = k.replace('_venue', '').split("_")
            for s in range(len(label)):
                if not dictionary.check(label[s]):
                    label[s] = label[s].upper()
                else:
                    label[s] = label[s].capitalize()
            label = " ".join(label)
            
            venue_msg += "\n"
            venue_msg += f"**{label} Venue** is set to : `{v}`"

        await msg_obj.edit(content=venue_msg)
        await interaction.response.defer()
        if None not in venue.values() and None not in wet_venue.values():
            input_event.set()

    async def wet_default_button_callback(interaction: Interaction):
        nonlocal wet_venue

        wet_venue = {s.group_name.lower().replace(" ","_")+"_wet_venue": default_wet_venue for s in wet_venue_select}

        wet_venue_msg = f"**Select the wet weather venue of the Routine Order**"
        for k, v in wet_venue.items():
            label = k.replace('_wet_venue', '').split("_")
            for s in range(len(label)):
                if not dictionary.check(label[s]):
                    label[s] = label[s].upper()
                else:
                    label[s] = label[s].capitalize()
            label = " ".join(label)
            
            wet_venue_msg += "\n"
            wet_venue_msg += f"**{label} Wet Weather Venue** is set to : `{v}`"

        await wet_msg_obj.edit(content=wet_venue_msg)
        await interaction.response.defer()
        if None not in venue.values() and None not in wet_venue.values():
            input_event.set()
    
    venue_button.callback = venue_button_callback
    default_button.callback = default_button_callback
    wet_default_button.callback = wet_default_button_callback
    for s in venue_select:
        venue_view.add_item(s)
    
    for s in wet_venue_select:
        wet_venue_view.add_item(s)
    
    venue_button_view.add_item(venue_button)
    venue_button_view.add_item(default_button)
    venue_button_view.add_item(wet_default_button)

    msg_obj = await ctx.send(content=venue_msg, view=venue_view)
    wet_msg_obj = await ctx.send(content=wet_venue_msg, view=wet_venue_view)
    await ctx.send(view=venue_button_view)

    await input_event.wait()
    return dict(venue, **wet_venue)

async def config_sergeants(ctx: Context) -> dict: 
    date_view = discord.ui.View()
    date_button = discord.ui.Button(
        style = discord.ButtonStyle.secondary,
        label = "Set dates and times for event"
    )

    dates = {"reporting_dt" : None, "dismissal_dt" : None, "reminder_dt" : None}

    msg = f"**Select the dates of the Routine Order**"
    for k, v in dates.items():
        msg += "\n"
        msg += f"**{k[:-3].capitalize()} Time** is set to : `{v}`"

    async def date_button_callback(interaction: Interaction):
        date_modal = discord.ui.Modal(title="Routine Order Date Information")
        date_modal.add_item(
            discord.ui.TextInput(
                label="Input the reporting date and time for event", 
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

            msg = f"**Select the dates of the Routine Order**"
            for k, v in dates.items():
                msg += "\n"
                msg += f"**{k[:-3].capitalize()} Time** is set to : `{v}`"
            
            await msg_obj.edit(content=msg)
            
            await interaction2.response.defer()

        date_modal.on_submit = date_modal_callback
        await interaction.response.send_modal(date_modal)

    date_button.callback = date_button_callback
    date_view.add_item(item=date_button)

    msg_obj = await ctx.send(content=msg, view=date_view)
    
    return dates