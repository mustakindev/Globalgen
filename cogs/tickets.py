# cogs/tickets.py
import discord
from discord import app_commands, ui
from discord.ext import commands
from cogs.utils import *

class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Ticket", emoji="🎟", style=discord.ButtonStyle.blurple, custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_ticket(interaction, "General Support")

    @discord.ui.button(label="VIP Support", emoji="💖", style=discord.ButtonStyle.green, custom_id="vip_ticket")
    async def vip_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_data = get_user_data(interaction.user.id)
        if not (user_data and (user_data.get('is_vip') or user_data.get('is_mega'))):
            return await interaction.response.send_message("💔 VIP Support is for VIP/Mega users only.", ephemeral=True)
        await self.handle_ticket(interaction, "VIP Support")

    @discord.ui.button(label="Stock Issues", emoji="📦", style=discord.ButtonStyle.red, custom_id="stock_ticket")
    async def stock_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_ticket(interaction, "Stock Issue")

    async def handle_ticket(self, interaction: discord.Interaction, ticket_type: str):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="🎟️ Tickets")
        if not category:
            category = await guild.create_category("🎟️ Tickets")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        # Add staff roles? You can customize this
        for role in guild.roles:
            if "staff" in role.name.lower() or "admin" in role.name.lower() or "mod" in role.name.lower():
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title=f"🎀 {ticket_type}",
            description=f"Hello {interaction.user.mention}! A staff member will assist you shortly.\n"
                        f"Type your issue below. Click buttons to manage this ticket.",
            color=get_color()
        )

        view = TicketControlView()
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)

class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close", emoji="🔒", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.send("🔒 This ticket will be deleted in 5 seconds...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="Claim", emoji="👑", style=discord.ButtonStyle.green, custom_id="claim_ticket")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.send(f"👑 {interaction.user.mention} has claimed this ticket!")
        button.disabled = True
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Delete", emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="delete_ticket")
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete()

class TicketsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticket", description="🎟 Setup or manage ticket system")
    @app_commands.describe(action="setup | panel")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ticket(self, interaction: discord.Interaction, action: str):
        if action == "setup":
            if not is_server_admin(interaction.guild.id, interaction.user.id) and interaction.user.id != interaction.guild.owner_id:
                return await interaction.response.send_message("💔 Only server owner/admins can setup tickets.", ephemeral=True)

            embed = discord.Embed(
                title="🎀 CutieGen Ticket System",
                description="Click a button below to open a ticket!\n"
                            "🎟️ General Support\n💖 VIP Support (VIP/Mega only)\n📦 Stock Issues",
                color=get_color()
            )
            view = TicketPanelView()
            await interaction.response.send_message(embed=embed, view=view)

        else:
            await interaction.response.send_message("💔 Unknown action. Use `setup`.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketsCog(bot))
    bot.add_view(TicketPanelView())
    bot.add_view(TicketControlView())
