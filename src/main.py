import os
import sys
from dotenv import load_dotenv

import asyncio

import discord
from discord.ext.commands import Bot
from discord.ext.commands.context import Context

import calendar
from datetime import datetime, timezone
import pytz

load_dotenv()
TOKEN = os.getenv("TOKEN")
DEFAULT_CHANNEL = os.getenv("DEFAULT_CHANNEL")

bot = Bot(intents=discord.Intents.all(), command_prefix="$")

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to discord at {datetime.now(pytz.timezone('Asia/Singapore')).strftime('%m/%d/%Y, %H:%M:%S')}")
    await bot.get_channel(int(DEFAULT_CHANNEL)).send(f"{bot.user} has connected to discord at {datetime.now(pytz.timezone('Asia/Singapore')).strftime('%m/%d/%Y, %H:%M:%S')}")

@bot.command(name="ping", help="Responds with the latency of the bot")
async def ping(ctx:Context):
    msgping = round(((datetime.now(timezone.utc) - ctx.message.created_at).microseconds)/1000)
    apiping = round(bot.latency*1000)
    await ctx.send(f"🏓Latency is {msgping}ms. API Latency is {apiping}ms")

@bot.command(name="clear", help="")
async def clear(ctx:Context, limit=-1):
    await ctx.reply("Are you sure you want to clear the chat? (Y/N)")
    user_id = ctx.author.id
    confirm = await bot.wait_for("message", check=lambda msg: msg.author.id == user_id)

    if confirm.content.lower() == "yes" or confirm.content.lower() == "y":
        if limit == -1:
            await ctx.channel.purge()
        else:
            await ctx.channel.purge(limit=limit+4)
        await ctx.send(f"{limit if limit > 0 else 'All'} message(s) cleared")
        await asyncio.sleep(2)
        await ctx.channel.purge(limit=1)

@bot.command(name="make_ro", help="Uses a template to fill in a routine order")
async def make_ro(ctx:Context):
    user_id = ctx.author.id
    ro_info = {}

    # set routine order date
    await ctx.reply("Set Routine Order date, reporting time and dismissal time (e.g. 01/01/2023 1530 1800)")
    while True:
        ro_date = await bot.wait_for("message", check=lambda msg: msg.author.id == user_id)
        ro_date = ro_date.content
        temp = ro_date.replace(" ", "/").split("/")
        await ctx.send(temp)
        if len(temp[0]) != 2 or len(temp[1]) != 2 or len(temp[2]) != 4 or len(temp[3]) != 4 or len(temp[4]) != 4:
            await ctx.send("Try again, invalid date and time format used.")
            continue
        
        ro_info["activity date"] = ro_date[:-10]
        ro_info["reporting time"] = ro_date[-9:-5]
        ro_info["dismissal time"] = ro_date[-4:]
        break

    # set reminder date and time
    await ctx.reply("Set reminder date and time (e.g. 01/01/2023 2200)")
    while True:
        remind_date = await bot.wait_for("message", check=lambda msg: msg.author.id == user_id)
        remind_date = remind_date.content
        temp = remind_date.replace(" ", "/").split("/")
        if len(temp[0]) != 2 or len(temp[1]) != 2 or len(temp[2]) != 4 or len(temp[3]) != 4:
            await ctx.send("Try again, invalid date and time format used.")
            continue
        
        ro_info["reminder date"] = remind_date[:-5]
        ro_info["reminder time"] = remind_date[-4:]
        break

    await ctx.send(ro_info)

@bot.command(name="make_calendar", help="Uses a template to fill in a routine order")
async def make_calendar(ctx:Context):
    now = datetime.now(pytz.timezone('Asia/Singapore')).timetuple()
    embed = discord.Embed(
        title="When is your stuff",
        color=discord.Color.blue(),
    )
    embed.set_author(
        name=ctx.author.display_name, 
        icon_url=ctx.author.avatar
    )
    cur_calendar = calendar.month(now[0], now[1]).split("\n")
    embed.add_field(
        name=f"{' '*cur_calendar[0].count(' ')}`{cur_calendar[0].strip()}`",
        value=f"`{cur_calendar[1]}`",
        inline=False
    )
    view = discord.ui.View()
    previous_month = discord.ui.Button(
        style=discord.ButtonStyle.primary,
        label="⏮️ Previous",
    )
    next_month = discord.ui.Button(
        style=discord.ButtonStyle.primary,
        label="Next ⏭️",
    )
    view.add_item(previous_month)
    view.add_item(next_month)
    await ctx.send(embed=embed, view=view)

bot.run(TOKEN)