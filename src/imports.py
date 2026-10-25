import json
import os
import subprocess
import re
import secrets
from pathlib import Path
from datetime import datetime, timezone
import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord import Embed
from discord.ui import Button, View
from dotenv import load_dotenv


intents = discord.Intents.all()
intents.members = True
intents.dm_messages = True
bot = commands.Bot(command_prefix='!!!', intents=intents)
stat_names = []


