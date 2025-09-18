# cogs/help.py
import discord
from discord import app_commands
from discord.ext import commands
from cogs.utils import *

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="🌸 Cute help menu")
    async def help(self, interaction: discord.Interaction):
        config = get_config()
        embed = discord.Embed(
            title="🌸 Welcome to CutieGen Help!",
            color=get_color(),
            timestamp=datetime.utcnow()
        )

        embed.add_field(
            name=f"{config['emojis']['gen']} Gen 🌸",
            value="`/gen <service>` — Generate accounts\n`/stock` — View stock",
            inline=False
        )
        embed.add_field(
            name=f"{config['emojis']['ticket']} Tickets 🎟",
            value="`/ticket setup` — Create ticket panel",
            inline=False
        )
        embed.add_field(
            name=f"{config['emojis']['admin']} Admin 👑",
            value="`/addstock`, `/setchannel`, `/givecredits`, etc.",
            inline=False
        )
        embed.add_field(
            name=f"{config['emojis']['owner']} Owner 💎",
            value="Global bot management (owner only)",
            inline=False
        )
        embed.add_field(
            name="🌟 VIP & Mega",
            value="Get perks like shorter cooldowns, bonus credits, priority access!",
            inline=False
        )

        embed.set_footer(text=config['branding']['footer'])
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
