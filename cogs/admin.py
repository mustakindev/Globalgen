# cogs/admin.py
import discord
from discord import app_commands
from discord.ext import commands
from cogs.utils import *

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setadmin", description="👑 Assign a Gen Admin (Owner Only)")
    @app_commands.describe(user="User to grant admin")
    async def setadmin(self, interaction: discord.Interaction, user: discord.Member):
        if interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("💔 Only server owner can assign admins.", ephemeral=True)

        conn = sqlite3.connect('database.sqlite')
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO server_admins (server_id, user_id) VALUES (?, ?)",
                  (interaction.guild.id, user.id))
        conn.commit()
        conn.close()

        await interaction.response.send_message(f"💖 {user.mention} is now a Gen Admin!", ephemeral=True)

    @app_commands.command(name="removeadmin", description="👑 Remove a Gen Admin (Owner Only)")
    @app_commands.describe(user="User to remove")
    async def removeadmin(self, interaction: discord.Interaction, user: discord.Member):
        if interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("💔 Only server owner can remove admins.", ephemeral=True)

        conn = sqlite3.connect('database.sqlite')
        c = conn.cursor()
        c.execute("DELETE FROM server_admins WHERE server_id = ? AND user_id = ?",
                  (interaction.guild.id, user.id))
        conn.commit()
        conn.close()

        await interaction.response.send_message(f"💔 {user.mention} is no longer a Gen Admin.", ephemeral=True)

    @app_commands.command(name="setchannel", description="👑 Set important bot channels")
    @app_commands.describe(channel_type="gen | ticket | log | stock", channel="Target channel")
    async def setchannel(self, interaction: discord.Interaction, channel_type: str, channel: discord.TextChannel):
        if not is_server_admin(interaction.guild.id, interaction.user.id) and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("💔 Only server admins or owner can set channels.", ephemeral=True)

        valid_types = ["gen", "ticket", "log", "stock"]
        if channel_type not in valid_types:
            return await interaction.response.send_message(f"💔 Invalid type. Use: {', '.join(valid_types)}", ephemeral=True)

        col_name = f"{channel_type}_channel"
        update_server_settings(interaction.guild.id, **{col_name: channel.id})

        await interaction.response.send_message(f"💖 {channel_type.title()} channel set to {channel.mention}", ephemeral=True)

    @app_commands.command(name="givecredits", description="👑 Give credits to a user (global)")
    @app_commands.describe(user="User to reward", amount="Amount of credits")
    async def givecredits(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if not is_server_admin(interaction.guild.id, interaction.user.id) and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("💔 Only server admins or owner can give credits.", ephemeral=True)

        if amount <= 0:
            return await interaction.response.send_message("💔 Amount must be positive.", ephemeral=True)

        current = get_user_data(user.id) or {}
        new_credits = current.get('credits', 0) + amount
        update_user_data(user.id, credits=new_credits)

        await interaction.response.send_message(f"💖 Gave {amount} credits to {user.mention}! They now have {new_credits}.", ephemeral=True)

    @app_commands.command(name="cooldown", description="👑 Set cooldown for a service")
    @app_commands.describe(service="Service name", seconds="Cooldown in seconds")
    async def cooldown(self, interaction: discord.Interaction, service: str, seconds: int):
        if not is_server_admin(interaction.guild.id, interaction.user.id) and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("💔 Only server admins or owner can set cooldowns.", ephemeral=True)

        settings = get_server_settings(interaction.guild.id)
        cooldowns = settings.get('cooldowns', {})
        cooldowns[service] = seconds
        update_server_settings(interaction.guild.id, cooldowns=str(cooldowns))

        await interaction.response.send_message(f"💖 Cooldown for `{service}` set to {seconds} seconds.", ephemeral=True)

    @app_commands.command(name="blacklistservice", description="👑 Disable a service in this server")
    @app_commands.describe(service="Service to disable")
    async def blacklistservice(self, interaction: discord.Interaction, service: str):
        if not is_server_admin(interaction.guild.id, interaction.user.id) and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("💔 Only server admins or owner can blacklist services.", ephemeral=True)

        settings = get_server_settings(interaction.guild.id)
        bl = settings.get('blacklisted_services', [])
        if service.lower() not in [s.lower() for s in bl]:
            bl.append(service.lower())
            update_server_settings(interaction.guild.id, blacklisted_services=','.join(bl))

        await interaction.response.send_message(f"💔 `{service}` is now disabled in this server.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
