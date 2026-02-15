import os
import subprocess
import time
import discord
import asyncio
import hashlib

# Shared State Object
class PlaybackState:
    def __init__(self):
        self.current_voice_client = None
        self.is_looping = False
        self.current_track_path = None
        self.total_duration = 0.0
        self.start_playback_time = 0.0
        self.elapsed_offset = 0.0
        self.is_seeking = False
        self.suppress_after_callback = False
        self.is_normalized = False
        self.optimized_files = {}  # filename -> is_optimized (bool)
        # Use absolute path for central cache in bot root
        self.bot_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.cache_dir = os.path.join(self.bot_root, ".phonograph_cache")

state = PlaybackState()

def get_audio_files(directory):
    """Returns a list of audio files in the given directory."""
    extensions = ('.mp3', '.wav', '.flac', '.m4a')
    try:
        return [f for f in os.listdir(directory) if f.lower().endswith(extensions)]
    except Exception:
        return []

def get_audio_duration(filepath):
    """Uses ffprobe to get the duration of an audio file in seconds."""
    try:
        cmd = [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', filepath
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Error getting duration: {e}")
        return 0

def format_time(seconds):
    """Formats seconds into MM:SS."""
    seconds = int(seconds)
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins:02d}:{secs:02d}"

async def play_audio_logic(bot, filepath, seek_to=0):
    """Core playback logic with support for seeking and duration tracking."""
    vc = state.current_voice_client
    if not vc:
        return

    state.current_track_path = filepath
    state.total_duration = get_audio_duration(filepath)
    state.elapsed_offset = seek_to
    
    if vc.is_playing() or vc.is_paused():
        state.suppress_after_callback = True
        vc.stop()

    def after_playing(error):
        if error:
            print(f'Player error: {error}')
        
        # If we are manually switching tracks or stopping, don't trigger the loop
        if state.suppress_after_callback:
            state.suppress_after_callback = False # Reset the flag
            return

        # If looping is enabled AND we didn't manually stop it
        if state.is_looping and state.current_track_path:
            bot.loop.call_soon_threadsafe(
                lambda: asyncio.run_coroutine_threadsafe(
                    play_audio_logic(bot, state.current_track_path), bot.loop
                )
            )

    try:
        # Check if a cached Opus version exists in the central directory
        cached_file = get_cache_path(filepath)
        
        # Audio transformation options
        # We need stereo and optional normalization
        filters = []
        if state.is_normalized:
            # Broadcast standard normalization (EBU R128)
            filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")
        
        filter_str = f"-af {','.join(filters)}" if filters else ""
        ffmpeg_options = f"-ac 2 {filter_str}" 
        before_args = f"-ss {seek_to}" if seek_to > 0 else None

        if os.path.exists(cached_file) and not state.is_normalized:
            # If we have a cache and DON'T need normalization, use the fast path
            print(f"[AudioEngine] Playing cached: {os.path.basename(cached_file)}")
            source = discord.FFmpegOpusAudio(cached_file, before_options=before_args)
        elif os.path.exists(cached_file) and state.is_normalized:
            # If we have cache but NEED normalization, we have to run it through opus decoder + filters
            print(f"[AudioEngine] Playing cached (Normalized): {os.path.basename(cached_file)}")
            source = discord.FFmpegPCMAudio(cached_file, options=ffmpeg_options, before_options=before_args)
        else:
            # No cache or normalization needed on raw file
            print(f"[AudioEngine] Transcoding: {os.path.basename(filepath)}")
            source = discord.FFmpegPCMAudio(filepath, options=ffmpeg_options, before_options=before_args)
        
        vc.play(source, after=after_playing)
        state.start_playback_time = time.time()
    except Exception as e:
        print(f"Playback error: {e}")

async def pause_logic():
    vc = state.current_voice_client
    if vc and vc.is_playing():
        state.elapsed_offset += (time.time() - state.start_playback_time)
        vc.pause()

async def resume_logic():
    vc = state.current_voice_client
    if vc and vc.is_paused():
        state.start_playback_time = time.time()
        vc.resume()

def get_cache_path(filepath):
    """
    Returns a unique path in the central cache for the given audio file.
    Uses MD5 hash of the absolute path to prevent collisions.
    """
    abs_path = os.path.abspath(filepath)
    path_hash = hashlib.md5(abs_path.encode('utf-8')).hexdigest()
    # Keep original filename for easier identification in the cache folder
    filename = os.path.basename(filepath)
    return os.path.join(state.cache_dir, f"{path_hash}_{filename}.opus")

def ensure_cache_dir():
    """Creates the central hidden cache directory if it doesn't exist."""
    if not os.path.exists(state.cache_dir):
        os.makedirs(state.cache_dir)
    return state.cache_dir

def is_file_optimized(filepath):
    """Checks if a file has a valid, up-to-date cached version in the central cache."""
    cached_file = get_cache_path(filepath)
    
    if not os.path.exists(cached_file):
        return False
        
    # Check if original is newer than cache
    if os.path.getmtime(filepath) > os.path.getmtime(cached_file):
        return False
        
    return True

def transcode_to_opus(filepath):
    """Transcodes a single file to Opus format in the central cache."""
    ensure_cache_dir()
    output_file = get_cache_path(filepath)
    
    # ffprobe/ffmpeg command to convert to Opus
    cmd = [
        'ffmpeg', '-y', '-i', filepath,
        '-c:a', 'libopus', '-b:a', '128k', '-ar', '48000', '-ac', '2',
        output_file
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except Exception as e:
        filename = os.path.basename(filepath)
        print(f"Transcoding error for {filename}: {e}")
        return False

def start_optimization_worker(directory, on_file_completed):
    """Starts a background thread to transcode all files in a directory."""
    import threading
    
    def worker():
        files = get_audio_files(directory)
        for filename in files:
            filepath = os.path.join(directory, filename)
            state.optimized_files[filename] = is_file_optimized(filepath)
            # Notify GUI of initial status
            on_file_completed(filename, state.optimized_files[filename])

        for filename in files:
            if not state.optimized_files[filename]:
                filepath = os.path.join(directory, filename)
                print(f"Optimizing: {filename}")
                success = transcode_to_opus(filepath)
                if success:
                    state.optimized_files[filename] = True
                    on_file_completed(filename, True)
        print("Optimization complete.")

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
