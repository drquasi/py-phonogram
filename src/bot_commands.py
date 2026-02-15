import os
import tkinter as tk
from tkinter import filedialog
from .audio_engine import state, play_audio_logic, pause_logic, resume_logic

def register_commands(bot):
    @bot.command()
    async def join(ctx):
        """Joins the user's voice channel."""
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            if ctx.voice_client:
                await ctx.voice_client.move_to(channel)
            else:
                await channel.connect()
            state.current_voice_client = ctx.voice_client
            await ctx.send(f"Joined {channel}. Phonograph Controller is ready!")
        else:
            await ctx.send("You need to be in a voice channel first!")

    @bot.command()
    async def play(ctx):
        """Opens a one-time file dialog and plays."""
        if not ctx.voice_client:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
                state.current_voice_client = ctx.voice_client
            else:
                return await ctx.send("You need to be in a voice channel first!")

        def select_file():
            root = tk.Tk()
            root.withdraw()
            path = filedialog.askopenfilename()
            root.destroy()
            return path

        file_path = await bot.loop.run_in_executor(None, select_file)
        if not file_path:
            return

        await play_audio_logic(bot, file_path)
        await ctx.send(f"Now playing (Stereo): {os.path.basename(file_path)}")

    @bot.command()
    async def loop(ctx):
        """Toggles audio looping."""
        state.is_looping = not state.is_looping
        status = "enabled" if state.is_looping else "disabled"
        await ctx.send(f"Looping is now **{status}**.")

    @bot.command()
    async def pause(ctx):
        """Pauses the current audio."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            await pause_logic()
            await ctx.send("Paused.")
        else:
            await ctx.send("Nothing is playing.")

    @bot.command()
    async def resume(ctx):
        """Resumes the current audio."""
        if ctx.voice_client and ctx.voice_client.is_paused():
            await resume_logic()
            await ctx.send("Resumed.")
        else:
            await ctx.send("Audio is not paused.")

    @bot.command()
    async def stop(ctx):
        """Stops the current audio."""
        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            state.current_track_path = None
            state.total_duration = 0
            state.elapsed_offset = 0
            ctx.voice_client.stop()
            await ctx.send("Stopped playback.")
        else:
            await ctx.send("Nothing is playing.")

    @bot.command(aliases=['disconnect'])
    async def leave(ctx):
        """Leaves the voice channel."""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            state.current_voice_client = None
            await ctx.send("Disconnected.")
        else:
            await ctx.send("I'm not in a voice channel.")
