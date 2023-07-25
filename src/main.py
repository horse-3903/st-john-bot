import os
from dotenv import load_dotenv

import asyncio

import discord
from discord.ext.commands import Bot
from discord.ext.commands.context import Context

from datetime import datetime, timezone
import pytz

from config import *

load_dotenv()
TOKEN = os.getenv("TOKEN")
DEFAULT_CHANNEL = os.getenv("DEFAULT_CHANNEL")

bot = Bot(intents=discord.Intents.all(), command_prefix="$")

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to discord at {datetime.now(pytz.timezone('Asia/Singapore')).strftime('%m/%d/%Y, %H:%M:%S')}")
    await bot.get_channel(int(DEFAULT_CHANNEL)).send(f"{bot.user} has connected to discord at `{datetime.now(pytz.timezone('Asia/Singapore')).strftime('%m/%d/%Y, %H:%M:%S')}`")

@bot.command(name="ping", help="Responds with the latency of the bot")
async def ping(ctx: Context):
    msgping = round(((datetime.now(timezone.utc) - ctx.message.created_at).microseconds)/1000)
    apiping = round(bot.latency*1000)
    await ctx.send(f"🏓Latency is `{msgping}ms`. API Latency is `{apiping}ms`")

@bot.command(name="clear", help=None, aliases=["clr"])
async def clear(ctx: Context, confirm=None, limit=-1):
    if confirm != "y": 
        await ctx.reply("Are you sure you want to clear the chat? (Y/N)")
        confirm_msg = await bot.wait_for("message", check=lambda msg: msg.author.id == ctx.author.id)
        confirm = confirm_msg.content.lower()

    if confirm == "y": 
        if limit == -1: 
            await ctx.channel.purge()
        else: 
            await ctx.channel.purge(limit=limit+4)
        after_msg = await ctx.send(f"{limit if limit > 0 else 'All'} message(s) cleared")
        await asyncio.sleep(2)
        await after_msg.delete()

@bot.command(name="create_routine_order", help="Uses a template to fill in a routine order", aliases=["cro", "create_ro"])
async def create_ro(ctx: Context):    
    # Query for dates and times
    res = await config_date(ctx=ctx)
    info = res
    
    # Query for groups involved 
    res = await config_groups(ctx=ctx, info=info)
    info = dict(info, **res)

    # Query for attire 
    res = await config_attire(ctx=ctx, info=info)
    info = dict(info, **res)

    # Query for venue
    res = await config_venue(ctx=ctx, info=info)
    info = dict(info, **res)    

    await ctx.send(f"LETS GO THIS SHIT WORKS : \n`{info}`")

bot.run(TOKEN)