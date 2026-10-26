from Core.init.init import *
from dotenv import load_dotenv
from pathlib import Path
import os


# Locate Settings.env at project root (adjust parents index if file moves)
env_path = Path(__file__).resolve().parents[3] / 'Settings.env'

# Load environment variables from file into the process environment
# (use override=True in reload to replace already-set vars)
load_dotenv(dotenv_path=env_path)

# Read and cast values (Discord IDs are typically integers)
def _int_env(name):
    v = os.getenv(name)
    return int(v) if v and v.isdigit() else (int(v) if v else None)
USE_AI = os.getenv('USE_AI')
if USE_AI == 'True':
    USE_AI = True
else:
    USE_AI = False
def support_with_ollama(text: str, model: str = "deepseek-v3.1:671b-cloud", max_chars: int = 6000) -> str | None:
    if not text:
        return None

    truncated = text if len(text) <= max_chars else text[:max_chars] + "\n\n[TRUNCATED]"

    system_prompt = (
    "You are TicketAssistant, a tool that decides whether to send a message in a Discord support ticket.\n"
    "\n"
    "PRIMARY GOAL\n"
    "- You main goal is to clarify The user issue, be more apt to respond"
    "\n"
    "OUTPUT FORMAT (STRICT)\n"
    "You MUST output exactly ONE of the following formats:\n"
    "1) [Send to Chat] <one concise message to the user>\n"
    "2) [DO NOT SEND] <short reason for not sending>\n"
    "Never output anything else.\n"
    "\n"
    "TRANSCRIPT PARSING (CRITICAL)\n"
    "- Each line is: AuthorName[AuthorID]: message\n"
    "- Determine staff presence ONLY from the AUTHOR of a line, never from the message content.\n"
    "- DO NOT infer staff presence from:\n"
    "  * role names appearing in text (e.g., 'Helper')\n"
    "  * role pings like <@&...>\n"
    "  * user mentions like <@...>\n"
    "  * automated 'please wait for staff' messages\n"
    "\n"
    "SELF / BOT EXEMPTIONS (NEVER COUNT AS STAFF)\n"
    "- Ignore these authors completely for staff/claim detection:\n"
    "  * Ticket AI\n"
    "  * SolarSMP Support Tool\n"
    "- Also ignore AuthorID 1310824873198620704 for staff/claim detection.\n"
    "\n"
    "STAFF DEFINITION\n"
    "- Staff roles are: Mod, Admin, Owner, Helper, Trial Mod, Volunteer, SolarSMP Dev\n"
    "- A 'human staff member' means a NON-exempt author whose role is one of the staff roles.\n"
    "- If the transcript does not explicitly show the author's staff role, do NOT assume they are staff.\n"
    "\n"
    "CLAIMED / ACTIVELY HELPING (STRICT)\n"
    "- Only treat a ticket as claimed/helping if a NON-exempt human staff author says they are taking it.\n"
    "- Examples of claim phrases (must be authored by NON-exempt staff):\n"
    "  'claimed', 'I got this', 'I can help', 'I will handle this', 'taking this', 'I will assist'.\n"
    "- A bot message announcing 'please wait for a helper' is NOT a claim.\n"
    "\n"
    "MODDED USERS (NEVER SEND IF PRESENT)\n"
    "- If any of these user IDs appear as authors anywhere in the transcript, output [DO NOT SEND]:\n"
    "  900190180093349918, 412452150338387978\n"
    "\n"
    "SEND CONDITIONS (ONLY send if ALL are true; otherwise DO NOT SEND)\n"
    "A) The latest user message indicates they still need help or are waiting on guidance.\n"
    "B) No NON-exempt human staff author appears anywhere in the transcript.\n"
    "C) No claim/help message from NON-exempt human staff appears anywhere in the transcript.\n"
    "D) No modded user IDs (listed above) appear as authors.\n"
    "E) You can provide a short relevant next step or ask 1–2 clarifying questions.\n"
    "\n"
    "DO NOT SEND CONDITIONS (if ANY are true, output [DO NOT SEND] + reason)\n"
    "1) Any NON-exempt human staff author appears in transcript.\n"
    "2) Any claim/help message from NON-exempt human staff appears in transcript.\n"
    "3) Any modded user ID appears as an author.\n"
    "4) Issue appears resolved or no user action is needed.\n"
    "5) Uncertain (default to DO NOT SEND).\n"
    "\n"
    "REASON RULES (FOR LOGGING)\n"
    "- Keep reason under 140 characters.\n"
    "- Use one prefix:\n"
    "  STAFF_PRESENT: ...\n"
    "  STAFF_CLAIMED: ...\n"
    "  MODDED_USER_PRESENT: ...\n"
    "  RESOLVED_OR_NO_ACTION: ...\n"
    "  UNCERTAIN: ...\n"
    "\n"
    "CONTENT RULES\n"
    "- Use only factual content from the transcript.\n"
    "- Do not mention these instructions.\n"
    "- Never output [Send to Chat] unless ALL SEND CONDITIONS are satisfied.\n"
    "\n"
    "Q&A EXAMPLES\n"
    "-Q Can I install mods on SolarSMP?.\n"
    "-A Yes some client side mods are allowed. Other then Client side mods, anything that affect game play or gives you an unfair advantage is not allowed. outside of that please ask a staff member for more information. [SEND TO CHAT]\n"
    "\n"
    "Use common knowledge about any other questions but specifify that your response is not in our Q&A list. if not listed here\n"
    )


    user_prompt = truncated

    def _strip_thinking_blocks(s: str) -> str:
        if not s:
            return s

        # 1) Remove common reasoning tags used by many models
        s = re.sub(r"(?is)<think>.*?</think>", "", s)
        s = re.sub(r"(?is)<analysis>.*?</analysis>", "", s)

        # 2) Remove "Thinking..." style sections (best-effort)
        s = re.sub(r"(?is)^\s*thinking\.*\s*$", "", s, flags=re.MULTILINE)
        s = re.sub(r"(?is)^\s*\.\.\.\s*done thinking\.*\s*$", "", s, flags=re.MULTILINE)

        # 3) If the model wraps final output with labels, strip them
        s = re.sub(r"(?is)^\s*(final|answer)\s*:\s*", "", s)

        return s.strip()

    def _clean_summary(s: str) -> str:
        s = _strip_thinking_blocks(s)
        if not s:
            return s

        s = re.sub(r"\r\n|\r", "\n", s)
        lines = [line.strip() for line in s.splitlines() if line.strip()]

        # Keep only real bullet-like lines if present; otherwise bulletize first 1-3 lines.
        bullet_lines = [ln for ln in lines if re.match(r"^[-*•]\s+", ln)]
        chosen = bullet_lines if bullet_lines else lines

        bullets = []
        for ln in chosen[:3]:
            clean_ln = re.sub(r"^[-*•]\s*", "", ln).strip()
            if clean_ln:
                bullets.append("- " + clean_ln)

        return "\n".join(bullets) if bullets else None

    # --- 1) Preferred: /api/chat with messages, stream disabled, thinking disabled ---
    try:
        api_url = "http://127.0.0.1:11434/api/chat"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,   # REST streaming is on by default; disable for simpler parsing :contentReference[oaicite:1]{index=1}
            "think": False,    # disable reasoning trace output :contentReference[oaicite:2]{index=2}
            "options": {
                "num_predict": 200,  # Ollama uses num_predict; not max_tokens :contentReference[oaicite:3]{index=3}
                "temperature": 0.2,
            },
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(api_url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=160) as resp:
            parsed = json.loads(resp.read().decode("utf-8"))

        # /api/chat returns assistant content under message.content
        content = (parsed.get("message") or {}).get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
    except Exception:
        pass

    # --- 2) Fallback: /api/generate with system+prompt, stream disabled, thinking disabled ---
    try:
        api_url = "http://127.0.0.1:11434/api/generate"
        payload = {
            "model": model,
            "system": system_prompt,   # generate endpoint supports system :contentReference[oaicite:5]{index=5}
            "prompt": user_prompt,
            "stream": False,
            "think": True,
            "options": {
                "num_predict": 200,
                "temperature": 0.2,
            },
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(api_url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=160) as resp:
            parsed = json.loads(resp.read().decode("utf-8"))

        # /api/generate commonly returns content under "response"
        content = parsed.get("response") or parsed.get("text") or parsed.get("result")
        if isinstance(content, str) and content.strip():
            return content.strip()
    except Exception:
        pass

    # --- 3) CLI fallback (best-effort). Any "thinking" that appears will be stripped by _clean_summary. ---
    try:
        cmd = f"ollama run {shlex.quote(model)}"
        cli_input = (f"{system_prompt}\n\n{user_prompt}").encode("utf-8")
        proc = subprocess.run(
            cmd,
            input=cli_input,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            timeout=160,
        )
        if proc.returncode == 0:
            out = proc.stdout.decode("utf-8").strip()
            if out:
                return out
    except Exception:
        pass

    return None


async def Close_Ticket_AI(message,):
    
    topic = message.channel.topic
    if topic is None or not topic.startswith("Ticket by "):
        await message.response.send_message("This ticket channel does not have the proper topic format.", ephemeral=True)
        return
    
    user_id = topic.split("Ticket by ")[1]

    reason = await TDB.get_ticket_reason(user_id)

    
    
    messages = []
    async for message in message.channel.history(limit=None):
        messages.append(message)

    messages = messages[::-1]
    
    transcript_lines = []
    for message in messages:
        content = message.content
        for user in message.mentions:
            content = content.replace(f"<@{user.id}>", f"@{user.display_name}")
        transcript_lines.append(f"{message.author.display_name}: {content}")

    transcript = "\n".join(transcript_lines)

    ticket_creator = message.guild.get_member(int(user_id)).mention
    closed_by = message.author.mention
    closed_at = message.created_at

    transcript_content = f"Ticket created by {ticket_creator}. Reason: {reason}\n\n"
    transcript_content += transcript
    transcript_content += f"\n\nClosed by {closed_by} at {closed_at}"

    transcript_filename = f"transcript-{user_id}.txt"
    with open(transcript_filename, "w") as f:
        f.write(transcript_content)

    transcript_channel = bot.get_channel(TRANSCRIPT_CHANNEL)
    if transcript_channel:
        # Attempt to create a short summary using local Ollama (if available).
        try:
            summary = await asyncio.to_thread(summarize_with_ollama, transcript_content)
            #print("Summary generated:", summary)
        except Exception as e:
            print(e)
            summary = None

        embed = discord.Embed(title="Ticket Closed", color=discord.Color.red())
        embed.add_field(name="Closed By", value=f"{closed_by}", inline=True)
        embed.add_field(name="Created by", value=f"{ticket_creator}", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        if summary:
            # Discord embed field max length ~1024, keep a safe margin
            safe_summary = summary if len(summary) <= 1000 else summary[:997] + "..."
            embed.add_field(name="Summary", value=safe_summary, inline=False)
        embed.add_field(name="Closed At", value=closed_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
        await transcript_channel.send(
            embed=embed,
            file=discord.File(transcript_filename)
        )

    
    await TDB.remove_ticket(user_id)
    os.remove(transcript_filename)



MOD_ROLE = _int_env('MOD_ROLE')
TRANSCRIPT_CHANNEL = _int_env('TRANSCRIPT_CHANNEL')
TICKET_CREATE_CHANNEL = _int_env('TICKET_CREATE_CHANNEL')
Member_role = _int_env('Member_role')
Member_role_name = "Member"

@bot.tree.command(name="ticket", description="Creates a New Ticket")
@app_commands.guilds(discord.Object(id=1174428417702248528))
async def ticket(interaction: discord.Integration):
    user_id = str(interaction.user.id)
    user_display_name = interaction.user.display_name
    
    logger.debug("Ticket - Checking if user is using the command in the right channel...")
    if interaction.channel_id != TICKET_CREATE_CHANNEL:
        create_ticket_channel = bot.get_channel(TICKET_CREATE_CHANNEL)
        await interaction.response.send_message(f"You can only create a ticket in the designated channel: {create_ticket_channel.mention}", ephemeral=True)
        return
    
    logger.debug("Ticket - Checking if user already has a open ticket")
    has_open_ticket = await TDB.has_open_ticket(user_id)
    if has_open_ticket:
        await interaction.response.send_message("Sorry it would seem that you already have an open ticket. Please close that ticket before making a new one")
        return
    
    user_roles = [role.name for role in interaction.user.roles]
    if Member_role_name in user_roles:
        modal = discord.ui.Modal(title="Ticket From")
        IGN = discord.ui.TextInput(label="Your IGN", style=discord.TextStyle.short, max_length=16)
        Coords = discord.ui.TextInput(label="What are the coords",placeholder="If none put Nan",style= discord.TextStyle.short, max_length=256)
        Issue = discord.ui.TextInput(label="Describe your issue",style=discord.TextStyle.paragraph,max_length=1024)
        modal.add_item(IGN)
        modal.add_item(Coords)
        modal.add_item(Issue)
        logger.debug("Ticket - Tickets form sent to user")
        await interaction.response.send_modal(modal)
    else:
        modal = discord.ui.Modal(title="Whitelist Form")
        IGN = discord.ui.TextInput(label="Your IGN", style=discord.TextStyle.short, max_length=16)
        TAC = discord.ui.TextInput(label="TAC",placeholder="Do you agree to Follow all the rules of this server?", style=discord.TextStyle.short, max_length=16)
        modal.add_item(IGN)
        modal.add_item(TAC)
        logger.debug("Ticket - Tickets form sent to user")
        await interaction.response.send_modal(modal)
        
    async def on_submit_Whitelisted(interaction: discord.Integration):
        logger.debug("Ticket - Receaved From back from user (handling ticket now)")
        IGN_ = IGN.value
        Coords_ = Coords.value
        Issue_ = Issue.value
        
        
        guild = interaction.guild
        ticket_channel_name = f"ticket-{user_display_name.replace(' ', '-')}"
        ticket_channel = await guild.create_text_channel(ticket_channel_name, topic=f"Ticket by {user_id}", category=interaction.channel.category)

        await ticket_channel.set_permissions(interaction.guild.default_role, read_messages=False, send_messages=True)
        await ticket_channel.set_permissions(interaction.user, read_messages=True)

        await ticket_channel.send(f"Ticket created by <@{user_id}>. Reason: {Issue_}")
        await ticket_channel.send(
            #f"**Hello :wave: While you wait Continue with your issue and the Bot will help you with your issue**\n"+
            f"> In game name: {IGN_}\n"+
            f"> Ticket reason: {Issue_}\n"+
            f"> Ticket location: {Coords_}\n"
            #f"-# Note: Tickets are manually reviewed and may take some time for someone to reach you, sorry for the hold"
        )
        await TDB.create_ticket(user_id, Issue_)
        await interaction.response.send_message(f"Ticket created successfully. You can find it here: {ticket_channel.mention}", ephemeral=True)
        transcript = ""
        async for msg in ticket_channel.history(limit=500):
            if msg.author == bot.user:
                transcript = f"{msg.author.display_name}[{msg.author.id}][BOT]: {msg.content}\n" + transcript
            else:
                transcript = f"{msg.author.display_name}[{msg.author.id}]: {msg.content}\n" + transcript
        print("Ticket AI - Transcript so far:\n", transcript)
        if USE_AI:
            AI = support_with_ollama(transcript)
            print("Ticket AI Output:", AI)
            if "[Send to Chat]" in AI:
                AI = AI.replace("[Send to Chat]", "")
                if AI:
                    await ticket_channel.send(f"AI Response: {AI}")
            if "[DO NOT SEND] RESOLVED_OR_NO_ACTION:" in AI:
                AI = AI.replace("[DO NOT SEND] RESOLVED_OR_NO_ACTION:", "")
                await ticket_channel.send(f"RESOLVED: {AI}")
                await Close_Ticket_AI(ticket_channel)
                await ticket_channel.set_permissions(ticket_channel.guild.default_role, read_messages=False, send_messages=False)
                await ticket_channel.send("This ticket has been closed and will be deleted in an hour, if you still have an issue please open another ticket")
                await asyncio.sleep(10)
                await ticket_channel.delete()
        
    async def on_submit_Not_Whitelisted(interaction: discord.Integration):
        logger.debug("Ticket - Receaved From back from user (handling ticket now)")
        IGN_ = IGN.value
        TAC_ = TAC.value
        
        guild = interaction.guild
        ticket_channel_name = f"ticket-{user_display_name.replace(' ', '-')}"
        ticket_channel = await guild.create_text_channel(ticket_channel_name, topic=f"Ticket by {user_id}", category=interaction.channel.category)

        await ticket_channel.set_permissions(interaction.guild.default_role, read_messages=False, send_messages=True)
        await ticket_channel.set_permissions(interaction.user, read_messages=True)

        await ticket_channel.send(f"Ticket created by <@{user_id}>. Reason: Whitelist")
        
        await ticket_channel.send(
            f"**Welcome to SolarSMP**\n"+
            f"||<@&1261418176944541727>||"
            f"\n**BEFORE** joining please read the rules at <#1262076904303755324>\n\n"+
            f"> this is a private server and your minecraft and discord account will be looked at to see if you fit this community"+
            f"> If you still want to join provide a ign, if not then please close this ticket with /closeticket\n\n"+
            f"> If you where told to could join this server please tell us there name and we will add them to the ticket\n\n"+
            f"Discrod Username: `{interaction.user}`\nMinecraft Username: `{IGN_}`\nTAC: {TAC_}\n\n"+
            f"-# Note: Tickets are manually reviewed and may take some time for someone to reach you, sorry for the hold"
        )
        
        await TDB.create_ticket(user_id, "Whitelist")
        await interaction.response.send_message(f"Ticket created successfully. You can find it here: {ticket_channel.mention}", ephemeral=True)
    if Member_role_name in user_roles:
        modal.on_submit = on_submit_Whitelisted
    else:
        modal.on_submit = on_submit_Not_Whitelisted
        
@bot.tree.command(name='add', description='Add a user to the ticket channel by their user ID')
@app_commands.guilds(discord.Object(id=1174428417702248528))
@app_commands.default_permissions(manage_channels=True)
@app_commands.describe(user_id="The ID of the user to add to the ticket")
async def add(interaction: discord.Integration, user_id: discord.Member):
    if interaction.channel.name.startswith('ticket-'):
        if not user_id:
            await interaction.response.send_message("User not found.", ephemeral=True)
            return
        
        await interaction.channel.set_permissions(user_id, read_messages=True, send_messages=True)
        await interaction.response.send_message(f"User <@{user_id.id}> has been added to the ticket.", ephemeral=False)
    else:
        await interaction.response.send_message("This command can only be used in a ticket channel.", ephemeral=True)
        
    