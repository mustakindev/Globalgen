# cogs/gen.py
import discord
from discord import app_commands
from discord.ext import commands
import random
from datetime import datetime, timedelta
import asyncio
from cogs.utils import *

class GenCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="gen", description="✨ Generate an account for a service!")
    @app_commands.describe(service="Which service to generate for?")
    async def gen(self, interaction: discord.Interaction, service: str):
        user_id = interaction.user.id
        server_id = interaction.guild.id

        # Security & Cooldown Checks
        if is_blacklisted(user_id):
            return await interaction.response.send_message("💔 You are globally blacklisted.", ephemeral=True)

        user_data = get_user_data(user_id) or {}
        if not user_data:
            update_user_data(user_id, credits=0)

        # Check cooldown
        last_gen = user_data.get('last_gen')
        if last_gen:
            last_gen_time = datetime.fromisoformat(last_gen)
            now = datetime.utcnow()

            # Get server-specific cooldown
            server_settings = get_server_settings(server_id)
            base_cooldown = server_settings['cooldowns'].get(service, get_config()['cooldowns']['default'])

            # Apply VIP/Mega modifiers
            if user_data.get('is_mega'):
                cooldown_seconds = 0
            elif user_data.get('is_vip'):
                cooldown_seconds = get_config()['cooldowns']['vip']
            else:
                cooldown_seconds = base_cooldown

            if cooldown_seconds > 0 and (now - last_gen_time).total_seconds() < cooldown_seconds:
                remaining = int(cooldown_seconds - (now - last_gen_time).total_seconds())
                return await interaction.response.send_message(
                    f"⏳ Please wait {format_cooldown(remaining)} before generating again.",
                    ephemeral=True
                )

        # Check if service is blacklisted in server
        if service.lower() in [s.lower() for s in server_settings['blacklisted_services']]:
            return await interaction.response.send_message(f"💔 `{service}` is disabled in this server.", ephemeral=True)

        # Load stock
        stock = load_stock(server_id, service)
        if not stock:
            return await interaction.response.send_message(f"💔 No stock available for `{service}`.", ephemeral=True)

        # Pick random account
        account = random.choice(stock)
        stock.remove(account)
        save_stock(server_id, service, stock)

        # Update user
        now_iso = datetime.utcnow().isoformat()
        update_user_data(user_id,
                        last_gen=now_iso,
                        total_gens=user_data.get('total_gens', 0) + 1,
                        credits=user_data.get('credits', 0) + (5 if user_data.get('is_vip') else 1))

        # Log
        log_gen(user_id, server_id, service, account)

        # Send embed
        config = get_config()
        embed = discord.Embed(
            title=f"{config['emojis']['gen']} CutieGen – Your Request is Ready!",
            color=get_color(user_data),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="💖 Service", value=service.title(), inline=False)
        embed.add_field(name="📦 Account", value=f"`{account}`", inline=False)
        embed.add_field(name="⏳ Cooldown", value=format_cooldown(cooldown_seconds), inline=True)
        rank = "Mega ✨" if user_data.get('is_mega') else "VIP 🌟" if user_data.get('is_vip') else "Standard 🐾"
        embed.add_field(name="👑 Rank", value=rank, inline=True)
        embed.set_footer(text=config['branding']['footer'], icon_url=config['branding'].get('thumbnail'))
        if logo := get_service_logo(service):
            embed.set_thumbnail(url=logo)

        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Log to server log channel
        if log_ch_id := server_settings.get('log_channel'):
            if log_ch := self.bot.get_channel(log_ch_id):
                log_embed = discord.Embed(
                    description=f"**{interaction.user}** generated `{service}`",
                    color=0x2ecc71
                )
                await log_ch.send(embed=log_embed)

async def setup(bot):
    await bot.add_cog(GenCog(bot))
