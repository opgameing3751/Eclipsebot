from src.imports import *
from src.globals import *

@bot.tree.command(name="invite",description="sends an invite message for new players to join the crafters.one server")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def invite(interaction: discord.Interaction):
    embed = discord.Embed(
        title="The Offical Eclipse SMP Server"
    )
    embed.add_field(
        name="Welcome", 
        value="You have been invited to the Eclipse SMP!"
    )
    
    embed.set_footer(text=f"Version: {version}")
    
    """image_path = "Data/Pfp_images/embed_img.png" 
    
    with open(image_path, "rb") as image_file:
        image = discord.File(image_file, filename="image.png")
        embed.set_image(url="attachment://image.png")"""
    
    button = Button(label="Join the Server", url="https://discord.gg/wNPWWNuW2v")  # Replace with your actual link
    
    # Create a view to hold the button
    view = View()
    view.add_item(button)
    
    
    # await interaction.response.send_message(embed=embed, file=image, view=view)
    await interaction.response.send_message(embed=embed, view=view)