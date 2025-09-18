# cogs/stats.py
import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
from cogs.utils import *

class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profile", description="🌸 View your global profile")
    async def profile(self, interaction: discord.Interaction):
        user_data = get_user_data(interaction.user.id) or {}
        config = get_config()

        embed = discord.Embed(
            title=f"🎀 {interaction.user.name}'s Profile",
            color=get_color(user_data),
            timestamp=datetime.utcnow()
        )

        credits = user_data.get('credits', 0)
        total_gens = user_data.get('total_gens', 0)

        embed.add_field(name="💖 Credits", value=credits, inline=True)
        embed.add_field(name="🌸 Total Gens", value=total_gens, inline=True)

        if user_data.get('is_mega'):
            until = user_data['mega_until']
            embed.add_field(name="✨ Mega Until", value=f"<t:{int(until.timestamp())}:R>", inline=False)
        elif user_data.get('is_vip'):
            until = user_data['vip_until']
            embed.add_field(name="🌟 VIP Until", value=f"<t:{int(until.timestamp())}:R>", inline=False)
        else:
            embed.add_field(name="👑 Rank", value="Standard 🐾", inline=False)

        if last_gen := user_data.get('last_gen'):
            lg_time = datetime.fromisoformat(last_gen)
            embed.add_field(name="⏳ Last Gen", value=f"<t:{int(lg_time.timestamp())}:R>", inline=False)

        embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.set_footer(text=config['branding']['footer'])

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="stats", description="👑 Server stats")
    async def stats(self, interaction: discord.Interaction):
        conn = sqlite3.connect('database.sqlite')
        c = conn.cursor()

        # Total gens in server
        c.execute("SELECT COUNT(*) FROM gen_history WHERE server_id = ?", (interaction.guild.id,))
        total_gens = c.fetchone()[0]

        # Most used service
        c.execute("SELECT service, COUNT(*) as cnt FROM gen_history WHERE server_id = ? GROUP BY service ORDER BY cnt DESC LIMIT 1", (interaction.guild.id,))
        row = c.fetchone()
        top_service = f"{row[0]} ({row[1]} gens)" if row else "None"

        # Active users (last 7 days)
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        c.execute("SELECT COUNT(DISTINCT user_id) FROM gen_history WHERE server_id = ? AND timestamp > ?", (interaction.guild.id, week_ago))
        active_users = c.fetchone()[0]

        conn.close()

        embed = discord.Embed(
            title="📊 Server Stats",
            color=get_color(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Total Gens", value=total_gens, inline=True)
        embed.add_field(name="Active Users (7d)", value=active_users, inline=True)
        embed.add_field(name="Top Service", value=top_service, inline=False)
        embed.set_footer(text=get_config()['branding']['footer'])

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="history", description="🌸 View user's gen history (global)")
    @app_commands.describe(user="User to check")
    async def history(self, interaction: discord.Interaction, user: discord.User):
        conn = sqlite3.connect('database.sqlite')
        c = conn.cursor()
        c.execute("SELECT service, account, timestamp FROM gen_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10", (user.id,))
        rows = c.fetchall()
        conn.close()

        if not rows:
            return await interaction.response.send_message(f"💔 {user} has no generation history.", ephemeral=True)

        lines = []
        for service, account, ts in rows:
            time_str = f"<t:{int(datetime.fromisoformat(ts).timestamp())}:R>"
            lines.append(f"**{service}** • `{account}` • {time_str}")

        embed = discord.Embed(
            title=f"🎀 {user.name}'s Gen History",
            description="\n".join(lines),
            color=get_color(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=get_config()['branding']['footer'])
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="leaderboard", description="🌸 Top users by gens or credits")
    @app_commands.describe(type="gens | credits")
    async def leaderboard(self, interaction: discord.Interaction, type: str = "gens"):
        conn = sqlite3.connect('database.sqlite')
        c = conn.cursor()

        if type == "credits":
            c.execute("SELECT user_id, credits FROM users ORDER BY credits DESC LIMIT 10")
            rows = c.fetchall()
            title = "💰 Top by Credits"
            value_key = "credits"
        else:
            c.execute("SELECT user_id, total_gens FROM users ORDER BY total_gens DESC LIMIT 10")
            rows = c.fetchall()
            title = "🌸 Top by Generations"
            value_key = "total_gens"

        conn.close()

        lines = []
        for i, (uid, val) in enumerate(rows, 1):
            user = self.bot.get_user(uid)
            name = user.name if user else f"Unknown User ({uid})"
            lines.append(f"**{i}.** {name} — `{val}`")

        embed = discord.Embed(
            title=title,
            description="\n".join(lines) if lines else "No data yet.",
            color=get_color(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=get_config()['branding']['footer'])
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(StatsCog(bot))
