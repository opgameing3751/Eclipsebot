

from src.imports import *
from src.globals import *

import os
import io
import discord
from datetime import datetime, timezone


async def send_ticket_transcript(interaction, tickets, bot):
    # Find the ticket associated with this channel
    ticket = tickets.get_ticket(interaction.channel.name)

    if ticket is None:
        print("Ticket not found for this channel.")
        return False

    # Get the transcript channel
    channel_id = int(os.getenv("transcript_channel"))
    transcript_channel = bot.get_channel(channel_id)

    if transcript_channel is None:
        transcript_channel = await bot.fetch_channel(channel_id)

    # Retrieve ALL messages, oldest first
    transcript = []
    message_count = 0

    async for message in interaction.channel.history(
        limit=None,
        oldest_first=True
    ):
        message_count += 1

        timestamp = message.created_at.strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )

        content = message.content or "[No text content]"

        transcript.append(
            f"[{timestamp}] "
            f"{message.author.name} ({message.author.id}):\n"
            f"{content}"
        )

        # Include attachment URLs
        for attachment in message.attachments:
            transcript.append(
                f"Attachment: {attachment.url}"
            )

        # Include embed contents
        for embed in message.embeds:
            if embed.title:
                transcript.append(f"Embed Title: {embed.title}")

            if embed.description:
                transcript.append(
                    f"Embed Description: {embed.description}"
                )

            for field in embed.fields:
                transcript.append(
                    f"{field.name}: {field.value}"
                )

        transcript.append("-" * 60)

    # Convert transcript into a TXT file
    transcript_text = "\n".join(transcript)

    file_data = io.BytesIO(
        transcript_text.encode("utf-8")
    )

    file_data.seek(0)

    transcript_file = discord.File(
        file_data,
        filename=f"{ticket['id']}.txt"
    )

    # Ticket timestamps
    opened_at = datetime.fromisoformat(ticket["opened_at"])
    closed_at = datetime.now(timezone.utc)

    # Create ticket information embed
    embed = discord.Embed(
        title="Ticket Closed",
        description=f"Transcript for ticket `{ticket['id']}`",
        color=discord.Color.red(),
        timestamp=closed_at
    )

    embed.add_field(
        name="Ticket ID",
        value=f"`{ticket['id']}`",
        inline=False
    )

    embed.add_field(
        name="Opened By",
        value=f"<@{ticket['user_id']}>",
        inline=True
    )

    embed.add_field(
        name="Closed By",
        value=interaction.user.mention,
        inline=True
    )

    embed.add_field(
        name="Opened At",
        value=discord.utils.format_dt(opened_at, "F"),
        inline=False
    )

    embed.add_field(
        name="Closed At",
        value=discord.utils.format_dt(closed_at, "F"),
        inline=False
    )

    embed.add_field(
        name="Total Messages",
        value=str(message_count),
        inline=True
    )

    embed.add_field(
        name="Ticket Channel",
        value=f"`{interaction.channel.name}`",
        inline=True
    )

    embed.set_footer(
        text=f"Ticket System • {ticket['id']}"
    )

    # Send the embed and TXT attachment together
    await transcript_channel.send(
        embed=embed,
        file=transcript_file
    )

    return True

@bot.tree.command(name="ticket",description="Creates a Ticket")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def createticket(interaction: discord.Interaction):
    if not TICKET_CREATE_CHANNEL:
        pass
    else:
        if interaction.channel_id != TICKET_CREATE_CHANNEL:
            create_ticket_channel = bot.get_channel(TICKET_CREATE_CHANNEL)
            print(create_ticket_channel)
            await interaction.response.send_message(f"You can only create a ticket in the designated channel: {create_ticket_channel.mention}", ephemeral=True)
            return
    UserRoles = interaction.user.roles
    
    #-----------------------------------------------------------------------------------------------------------------------------------------#
    #Checks if user is already whitelisted and then sends them the ticket form
    if discord.utils.get(interaction.user.roles, id=Whitelist_role):
        modal = discord.ui.Modal(title="Ticket Form")
        
        IGN = discord.ui.TextInput(label="Your IGN", style=discord.TextStyle.short, max_length=16)
        Coords = discord.ui.TextInput(label="What are the coords",placeholder="If none put Nan",style= discord.TextStyle.short, max_length=256)
        Issue = discord.ui.TextInput(label="Describe your issue",style=discord.TextStyle.paragraph,max_length=1024)
        modal.add_item(IGN)
        modal.add_item(Coords)
        modal.add_item(Issue)
        await interaction.response.send_modal(modal)
    

    else:
        modal = discord.ui.Modal(title="Whitelist Form")
        IGN = discord.ui.TextInput(label="Your IGN", style=discord.TextStyle.short, max_length=16)
        TAC = discord.ui.TextInput(label="TAC",placeholder="Do you agree to Follow all the rules of this server?", style=discord.TextStyle.short, max_length=4)
        modal.add_item(IGN)
        modal.add_item(TAC)
        await interaction.response.send_modal(modal)
    
    async def WhitelistTicket(interaction: discord.Integration):
        IGN_ = IGN.value
        TAC_ = TAC.value
        ticket = tickets.create_ticket(
            user_id=interaction.user.id,
            username=interaction.user.name,
            guild_id=interaction.guild_id
        )
        ticket_channel = await interaction.guild.create_text_channel(ticket["id"], topic=f"Ticket by {ticket['username']}", category=interaction.channel.category)
        await ticket_channel.set_permissions(interaction.guild.default_role, read_messages=False, send_messages=True)
        await ticket_channel.set_permissions(interaction.user, read_messages=True)
        await ticket_channel.send(
            f"**Welcome to Eclips SMP**\n"+
            f"||<@&1261418176944541727>||"
            f"\n**BEFORE** joining please read the rules at <#1548427583018766469>\n\n"+
            f"> this is a whitelist server and your minecraft and discord account will be looked at to see if you fit this community\n\n"+
            f"> If you still want to join provide a ign, if not then please close this ticket with /closeticket\n\n"+
            f"> If you where told to could join this server please tell us there name and we will add them to the ticket\n\n"+
            f"Discrod Username: `{interaction.user}`\nMinecraft Username: `{IGN_}`\nTAC: {TAC_}\n\n"+
            f"-# Note: Tickets are manually reviewed and may take some time for someone to reach you, sorry for the hold"
        )
        
        tickets.update_ticket(ticket["id"],channel_id=ticket_channel.id)
        await interaction.response.send_message("Ticket has been created here " + ticket_channel.mention)
    
    async def IssueTicket(interaction: discord.Integration):
        IGN_ = IGN.value
        Coords_ = Coords.value
        Issue_ = Issue.value
    
        ticket = tickets.create_ticket(
            user_id=interaction.user.id,
            username=interaction.user.name,
            guild_id=interaction.guild_id
        )
        ticket_channel = await interaction.guild.create_text_channel(ticket["id"], topic=f"Ticket by {ticket['username']}", category=interaction.channel.category)
        await ticket_channel.set_permissions(interaction.guild.default_role, read_messages=False, send_messages=True)
        await ticket_channel.set_permissions(interaction.user, read_messages=True)
        await ticket_channel.send(
            f"**Someone will be with you shortly, please provide any releavent info you may want to share to us about this issue\n\n If this is a player rebort please post as much information you can regarding the concern**\n"+
            f"> In game name: {IGN_}\n"+
            f"> Ticket reason: {Issue_}\n"+
            f"> Ticket location: {Coords_}\n"
            f"-# Note: Tickets are manually reviewed and may take some time for someone to reach you, sorry for the hold"
        )
        tickets.update_ticket(ticket["id"],channel_id=ticket_channel.id)
        await interaction.response.send_message("Ticket has been created here " + ticket_channel.mention)
    
    
    if discord.utils.get(interaction.user.roles, id=Whitelist_role):
        modal.on_submit = IssueTicket
    else:
        modal.on_submit = WhitelistTicket
    
    

@bot.tree.command(name='add', description='Add a user to the ticket channel by their user ID')
@app_commands.default_permissions(manage_channels=True)
@app_commands.describe(user_id="The ID of the user to add to the ticket")
async def add(interaction: discord.Integration, user_id: discord.Member):
    ticket = tickets.get_ticket(interaction.channel.name)
    if ticket:
        if not user_id:
            await interaction.response.send_message("User not found.", ephemeral=True)
            return
        
        await interaction.channel.set_permissions(user_id, read_messages=True, send_messages=True)
        await interaction.response.send_message(f"User <@{user_id.id}> has been added to the ticket.", ephemeral=False)
    else:
        await interaction.response.send_message("This command can only be used in a ticket channel.", ephemeral=True)
    
@bot.tree.command(name='remove', description='Remove a user from the ticket channel by mention')
@app_commands.default_permissions(manage_channels=True)
@app_commands.describe(user_id="The ID of the user to add to the ticket")
async def remove(interaction: discord.Integration, user_id: discord.Member):
    ticket = tickets.get_ticket(interaction.channel.name)
    if ticket:
        if not user_id:
            await interaction.response.send_message("User not found.", ephemeral=True)
            return
        
        await interaction.channel.set_permissions(user_id, read_messages=False, send_messages=False)
        await interaction.response.send_message(f"User <@{user_id.id}> has been removed from the ticket.", ephemeral=False)
    else:
        await interaction.response.send_message("This command can only be used in a ticket channel.", ephemeral=True)
    
    
    
@bot.tree.command(name="closeticket",description="Closes a Ticket")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def closeticket(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    success = await send_ticket_transcript(
        interaction,
        tickets,
        bot
    )

    if not success:
        await interaction.followup.send(
            "Could not find the ticket.",
            ephemeral=True
        )
        return

    # Find the ticket ID
    ticket = tickets.get_ticket(interaction.channel.name)

    # Remove ticket from the JSON file
    tickets.close_ticket(ticket["id"])
    await interaction.followup.send(
            "Ticket has been closed and the transcript has been sent.",
            ephemeral=True
        )
    await asyncio.sleep(10)  # Give some time for the followup message to be sent before deleting the channel
    # Delete the ticket channel
    await interaction.channel.delete()
    