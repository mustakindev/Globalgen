# cogs/owner.py
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from cogs.utils import *

class OwnerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        config = get_config()
        return interaction.user.id == config['bot']['owner_id']

    @app_commands.command(name="botinfo", description="💎 Show bot stats")
    async def botinfo(self, interaction: discord.Interaction):
        config = get_config()
        embed = discord.Embed(
            title="💎 CutieGen — Bot Info",
            color=get_color(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Servers", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Users", value=len(self.bot.users), inline=True)
        embed.add_field(name="Version", value="1.0.0 ✨", inline=True)
        embed.set_footer(text="Made by Mustakin 💎")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="servers", description="💎 List all servers and stock")
    async def servers(self, interaction: discord.Interaction):
        config = get_config()
        lines = []
        for guild in self.bot.guilds:
            services_dir = os.path.join(config['paths']['services_dir'], str(guild.id))
            total_accounts = 0
            if os.path.exists(services_dir):
                for file in os.listdir(services_dir):
                    if file.endswith('.txt'):
                        total_accounts += len(load_stock(guild.id, file[:-4]))
            lines.append(f"**{guild.name}** (`{guild.id}`): {total_accounts} accounts")

        embed = discord.Embed(
            title="💎 All Servers",
            description="\n".join(lines) if lines else "No servers.",
            color=get_color()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="broadcast", description="💎 Send message to all servers")
    @app_commands.describe(message="Message to broadcast")
    async def broadcast(self, interaction: discord.Interaction, message: str):
        config = get_config()
        embed = discord.Embed(
            title="🎀 Announcement from CutieGen",
            description=message,
            color=get_color(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=config['branding']['footer'])

        sent = 0
        for guild in self.bot.guilds:
            # Try system channel, then first text channel
            channel = guild.system_channel or next((ch for ch in guild.text_channels if ch.permissions_for(guild.me).send_messages), None)
            if channel:
                try:
                    await channel.send(embed=embed)
                    sent += 1
                except:
                    pass

        await interaction.response.send_message(f"💎 Broadcast sent to {sent} servers.", ephemeral=True)

    @app_commands.command(name="blacklist", description="💎 Globally blacklist a user")
    @app_commands.describe(user="User to blacklist")
    async def blacklist(self, interaction: discord.Interaction, user: discord.User):
        conn = sqlite3.connect('database.sqlite')
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO global_blacklist (user_id) VALUES (?)", (user.id,))
        conn.commit()
        conn.close()
        await interaction.response.send_message(f"💔 {user} has been globally blacklisted.", ephemeral=True)

    @app_commands.command(name="whitelist", description="💎 Remove user from global blacklist")
    @app_commands.describe(user="User to whitelist")
    async def whitelist(self, interaction: discord.Interaction, user: discord.User):
        conn = sqlite3.connect('database.sqlite')
        c = conn.cursor()
        c.execute("DELETE FROM global_blacklist WHERE user_id = ?", (user.id,))
        conn.commit()
        conn.close()
        await interaction.response.send_message(f"💖 {user} has been removed from global blacklist.", ephemeral=True)

    @app_commands.command(name="reload", description="💎 Reload all cogs and config")
    async def reload(self, interaction: discord.Interaction):
        config = get_config()  # Reload config
        for cog in list(self.bot.cogs.keys()):
            await self.bot.reload_extension(f"cogs.{cog.lower()}")
        await interaction.response.send_message("💎 All cogs reloaded!", ephemeral=True)

    @app_commands.command(name="shutdown", description="💎 Shut down the bot")
    async def shutdown(self, interaction: discord.Interaction):
        await interaction.response.send_message("💤 Shutting down...", ephemeral=True)
        await self.bot.close()

    @app_commands.command(name="setvip", description="💎 Grant VIP status to user")
    @app_commands.describe(user="User", days="Duration in days")
    async def setvip(self, interaction: discord.Interaction, user: discord.User, days: int):
        until = datetime.utcnow() + timedelta(days=days)
        update_user_data(user.id, vip_until=until.isoformat())
        await interaction.response.send_message(f"🌟 {user} is now VIP for {days} days!", ephemeral=True)

    @app_commands.command(name="setmega", description="💎 Grant Mega status to user")
    @app_commands.describe(user="User", days="Duration in days")
    async def setmega(self, interaction: discord.Interaction, user: discord.User, days: int):
        until = datetime.utcnow() + timedelta(days=days)
        update_user_data(user.id, mega_until=until.isoformat())
        await interaction.response.send_message(f"✨ {user} is now MEGA for {days} days!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(OwnerCog(bot))
