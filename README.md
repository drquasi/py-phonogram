# Phonograph - Native Windows Discord Music Bot

As a dungeon master in DnD, I had one issue with music bots on Discord, and that was the fact that they only took links from online. 
What I needed was a way to play music from audio files on my own machine, which meant self hosting.

This bot was created to do that. Once setup, you can play mp3s, wavs, flacs, m4as on your PC directly into a VC through the bot.
There's a UI for you to easily switch around songs, too. No discord commands needed!!

## Key Features

- **Background Audio Optimization**: Automatically transcodes files to high-quality Opus in the background for instant, lag-free playback.
- **Smart Disk Cache**: Persistent central cache (`.phonograph_cache`) ensures optimized tracks never need to be processed twice.
- **Normalization**: Real-time `loudnorm` filter (EBU R128) ensures consistent volume across all tracks!
- **Precise Seeking & Progress**: Smooth progress tracking and instant seeking via a native Windows-style slider!
- **Looping & Controls**: Easily toggle looping and manage playback via the ribbon-style toolbar!

## Installation

### 1. Prerequisites
- **Python 3.8+**
- **FFmpeg**: Must be installed and added to your system's PATH. ([Download here](https://ffmpeg.org/download.html))
- **A Discord Bot Token**: Create one at the [Discord Developer Portal](https://discord.com/developers/applications).

### 2. Setup
1. Clone this repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to a new file named `.env` and paste your Discord token:
   ```env
   DISCORD_TOKEN=your_token_goes_here
   ```

## How to Use

Double-click **`run_phonograph.bat`** (Windows) or run:
```bash
python -m src.phonograph
```

### GUI Features
- **Address Bar**: Type or paste a directory path and press **Enter** to navigate instantly.
- **Browse Button**: Use the classic folder picker to switch directories.
- **Playback Ribbon**: manage Loop, Normalisation, and Pause/Resume states.
- **File List**: Double-click a file (`📄`) to play. Tracks are marked as `[Optimised]` once cached.

### Discord Commands
- `!join`: Connects the bot to your current voice channel.
- `!play`: Opens a file dialog on your host machine to pick a song.
- `!pause` / `!resume`: Toggle audio playback.
- `!loop`: Toggles track looping.
- `!leave`: Disconnects the bot from voice.


Mainly built for personal use, please don't expect too much heh