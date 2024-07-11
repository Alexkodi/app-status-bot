import os
import discord
import json
from dotenv import load_dotenv
from discord.ext import tasks
from discord.ext.commands import Bot, CommandNotFound
from subprocess import check_output, CalledProcessError, run
from datetime import datetime

# Wczytanie zmiennych środowiskowych
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

# Bot funkcjonalności
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

# Prefix
bot = Bot(command_prefix="#", intents=intents)

# Przelicznik czasu
def format_uptime(start_time):
    uptime = datetime.now() - datetime.fromtimestamp(start_time / 1000)
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return f"{days}d {hours}h {minutes}m {seconds}s"

# Zaczytywanie statusu
async def get_pm2_status():
    try:
        output = check_output(['pm2', 'jlist'])
        processes = json.loads(output)
        return processes
    except (CalledProcessError, json.JSONDecodeError) as e:
        print(f"Error fetching PM2 status: {e}")
        return []

# Start
@bot.event
async def on_ready():
    print(f'Bot is ready as {bot.user}')
    send_pm2_status.start()

# Petla do wysyłania podsumowań
@tasks.loop(hours=1)
async def send_pm2_status():
    processes = await get_pm2_status()
    if not processes:
        return

    status_message = "\n\n".join([
        f"""__**{proc['name']}**__
        **Uptime:** {format_uptime(proc['pm2_env']['pm_uptime'])}
        **Status:** {proc['pm2_env']['status']}
        **CPU:** {proc['monit']['cpu']}%
        **Memory:** {(proc['monit']['memory'] / 1024 / 1024):.2f} MB"""
        for proc in processes
    ])

    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(status_message)
    else:
        print('Channel not found')

# Polecenia
@bot.command(name='start')
async def pm2_start(ctx, name: str):
    result = run(['pm2', 'start', name], capture_output=True, text=True)
    await ctx.send(f"```{result.stdout}```")

@bot.command(name='stop')
async def pm2_stop(ctx, name: str):
    result = run(['pm2', 'stop', name], capture_output=True, text=True)
    await ctx.send(f"```{result.stdout}```")

@bot.command(name='restart')
async def pm2_stop(ctx, name: str):
    result = run(['pm2', 'restart', name], capture_output=True, text=True)
    await ctx.send(f"```{result.stdout}```")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        await ctx.send("""Command not found. 
                       Available commands are:
                       #start {name},
                       #stop {name},
                       #restart {name}""")
    else:
        raise error

bot.run(TOKEN)