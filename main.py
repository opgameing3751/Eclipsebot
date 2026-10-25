from src.imports import *

print("--------System Info Fetched--------")
try:
    # Run screenfetch and filter out ASCII art
    result = subprocess.run("screenfetch -p", shell=True, capture_output=True, text=True)

    if result.returncode != 0 or not result.stdout.strip():  # If screenfetch fails, fallback to neofetch
        print("screenfetch failed, trying neofetch")
        raise Exception("screenfetch failed")
except:  # If screenfetch fails, run neofetch
    print("running neofetch")
    result = subprocess.run("neofetch", shell=True, capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():  # If neofetch also fails
        print("Failed to fetch system info.")

# Print the output with color codes preserved
print(result.stdout, end="")

print("--------Importing Commands--------")
from src.CommandImports import *


print("--------Starting--------")

load_dotenv("data/config/config.env")

TOKEN = os.getenv("TOKEN")
print("loaded token: " + TOKEN)

if TOKEN == None:
    print("token is invalid, please check and try again")
    exit()
    
@bot.event
async def on_ready():
    print("Bot name set to: " + bot.user.name)
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        #logger.error(f"Error in on_ready(): {e}")
        print(e)
 
    print("--------Started Bot--------")








if __name__ == "__main__":
    bot.run(TOKEN)