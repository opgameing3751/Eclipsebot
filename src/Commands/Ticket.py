from src.imports import *
from src.globals import *



@bot.tree.command(name="ticket",description="Creates a Ticket")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def createticket(interaction: discord.Interaction):
    # if interaction.channel_id != TICKET_CREATE_CHANNEL:
            # create_ticket_channel = bot.get_channel(TICKET_CREATE_CHANNEL)
            # await interaction.response.send_message(f"You can only create a ticket in the designated channel: {create_ticket_channel.mention}", ephemeral=True)
            # return
    ticket = tickets.create_ticket(
        user_id=interaction.user.id,
        username=interaction.user.name,
        guild_id=interaction.guild_id
    )
    
    ticket_channel = await interaction.guild.create_text_channel(ticket["id"], topic=f"Ticket by {ticket["username"]}", category=interaction.channel.category)
    await ticket_channel.set_permissions(interaction.guild.default_role, read_messages=False, send_messages=True)
    await ticket_channel.set_permissions(interaction.user, read_messages=True)
    await ticket_channel.send(
        f"Ticket created by <@{ticket['user_id']}>.\n",
        "This is a test ticket"
        )
    
    tickets.update_ticket(ticket["id"],channel_id=ticket_channel.id)
    await interaction.response.send_message("Ticket create has been created here " + ticket_channel.mention)
    