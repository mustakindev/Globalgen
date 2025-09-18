# bot.py
import discord
from discord.ext import commands
import yaml
import os
import asyncio
from cogs.utils import setup_database, get_config

# Load config
config = get_config()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix=config['bot']['prefix'],
    intents=intents,
    help_command=None
)

@bot.event
async def on_ready():
    print(f"🌸 {config['branding']['name']} is online! Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Game(name=config['bot']['activity']))
    # Ensure services dir exists
    os.makedirs(config['paths']['services_dir'], exist_ok=True)
    # Setup DB if not exists
    await setup_database()

# Load all cogs
async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('__'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

async def main():
    async with bot:
        await load_cogs()
        await bot.start(config['bot']['token'])

if __name__ == "__main__":
    asyncio.run(main())
