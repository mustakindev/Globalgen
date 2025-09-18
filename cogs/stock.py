# cogs/stock.py
import discord
from discord import app_commands
from discord.ext import commands
from cogs.utils import *

class StockCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="addstock", description="👑 Add accounts to server stock (Admin Only)")
    @app_commands.describe(service="Service name", file="Upload .txt file with accounts")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def addstock(self, interaction: discord.Interaction, service: str, file: discord.Attachment):
        if not is_server_admin(interaction.guild.id, interaction.user.id) and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("💔 Only server admins or owner can manage stock.", ephemeral=True)

        if not file.filename.endswith('.txt'):
            return await interaction.response.send_message("💔 Please upload a .txt file.", ephemeral=True)

        content = await file.read()
        accounts = content.decode('utf-8').splitlines()
        accounts = [a.strip() for a in accounts if a.strip()]

        if not accounts:
            return await interaction.response.send_message("💔 No valid accounts found.", ephemeral=True)

        current_stock = load_stock(interaction.guild.id, service)
        current_stock.extend(accounts)
        save_stock(interaction.guild.id, service, current_stock)

        await interaction.response.send_message(f"💖 Added {len(accounts)} accounts to `{service}` stock!", ephemeral=True)

    @app_commands.command(name="clearstock", description="👑 Clear stock for a service (Admin Only)")
    @app_commands.describe(service="Service to clear")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def clearstock(self, interaction: discord.Interaction, service: str):
        if not is_server_admin(interaction.guild.id, interaction.user.id) and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("💔 Only server admins or owner can manage stock.", ephemeral=True)

        save_stock(interaction.guild.id, service, [])
        await interaction.response.send_message(f"💔 Cleared all stock for `{service}`.", ephemeral=True)

    @app_commands.command(name="stock", description="🌸 View current server stock")
    async def stock(self, interaction: discord.Interaction):
        server_id = interaction.guild.id
        config = get_config()
        services_dir = os.path.join(config['paths']['services_dir'], str(server_id))

        if not os.path.exists(services_dir):
            return await interaction.response.send_message("💔 No stock uploaded yet.", ephemeral=True)

        services = []
        for file in os.listdir(services_dir):
            if file.endswith('.txt'):
                service_name = file[:-4]
                count = len(load_stock(server_id, service_name))
                services.append(f"**{service_name.title()}**: `{count}` accounts")

        if not services:
            return await interaction.response.send_message("💔 No stock available.", ephemeral=True)

        embed = discord.Embed(
            title="🎀 Current Stock",
            description="\n".join(services) or "None",
            color=get_color(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=config['branding']['footer'])
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(StockCog(bot))
