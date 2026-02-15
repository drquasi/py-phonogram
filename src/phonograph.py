import os
import ctypes

# Fix for High DPI scaling on Windows
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2) # 2 = PER_MONITOR_DPI_AWARE
except Exception:
    pass # Non-Windows or older Windows versions
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import threading
import customtkinter as ctk

# Import modular components
from .audio_engine import state
from .gui_controller import PhonographGUI
from .bot_commands import register_commands

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Initialize bot with necessary intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Register Discord Commands
register_commands(bot)

def run_gui(bot):
    """Launches the tkinter GUI."""
    root = ctk.CTk()
    # Pass both the root and the bot instance for cross-module communication
    gui = PhonographGUI(root, bot)
    root.mainloop()

@bot.event
async def on_ready():
    print(f'[Phonograph] Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('[Phonograph] Controller is active.')
    
    # Start the GUI in a separate thread
    gui_thread = threading.Thread(target=run_gui, args=(bot,), daemon=True)
    gui_thread.start()

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN not found in .env file.")
    else:
        bot.run(TOKEN)
