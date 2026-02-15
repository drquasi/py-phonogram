import os
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
import time
import asyncio
from .audio_engine import state, get_audio_files, play_audio_logic, pause_logic, resume_logic, format_time, start_optimization_worker

# Set appearance mode
ctk.set_appearance_mode("Dark")

# =============================================================================
# Windows 10 Dark Mode Theme Constants
# =============================================================================
WIN_BG = "#191919"         # Main window background
WIN_TOOLBAR = "#2B2B2B"    # Ribbon / Address bar background
WIN_ACCENT = "#0078D4"     # Windows Blue
WIN_TEXT = "#FFFFFF"       # Primary text
WIN_MUTED = "#A0A0A0"      # Secondary / Muted text
WIN_HOVER = "#333333"      # Item hover (List/Buttons)
WIN_SELECT = "#444444"     # Item selection / Scrollbar hover
WIN_BORDER = "#3E3E3E"     # Border highlights
WIN_GREEN = "#107C10"      # Status: Optimized (Green)
WIN_WARNING = "#F0AD4E"    # Status: Warning (Orange)

FONT_MAIN = ("Segoe UI", 11)
FONT_BOLD = ("Segoe UI", 11, "bold")
FONT_STATUS = ("Segoe UI", 10)

class PhonographGUI:
    def __init__(self, root, bot):
        self.root = root
        self.bot = bot
        self.root.title("Phonograph - File Explorer")
        self.root.geometry("900x650") 
        self.root.configure(fg_color=WIN_BG)
        
        self.current_dir = os.getcwd()
        self.file_list = [] # Store raw filenames
        self.track_buttons = {} # filename -> ctk button
        
        # Toolbar Row (Mimics Explorer Ribbon/Address Bar)
        self.toolbar = ctk.CTkFrame(root, height=50, fg_color=WIN_TOOLBAR, corner_radius=0, border_width=1, border_color=WIN_BORDER)
        self.toolbar.pack(fill=tk.X, padx=0, pady=0)
        
        # Branding / "Logo"
        self.title_label = ctk.CTkLabel(self.toolbar, text="Phonograph", font=FONT_BOLD, text_color=WIN_TEXT)
        self.title_label.pack(side=tk.LEFT, padx=(20, 30), pady=12)
        
        # Address Bar Style Folder Info (Usable)
        self.address_frame = ctk.CTkFrame(self.toolbar, fg_color=WIN_BG, height=30, corner_radius=0, border_width=1, border_color=WIN_BORDER)
        self.address_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=10)
        
        self.folder_icon = ctk.CTkLabel(self.address_frame, text=" 📂 ", font=FONT_MAIN, text_color=WIN_MUTED, fg_color="transparent")
        self.folder_icon.pack(side=tk.LEFT, padx=(5, 0))
        
        self.address_entry = ctk.CTkEntry(self.address_frame, fg_color="transparent", border_width=0, font=FONT_MAIN, 
                                          text_color=WIN_TEXT, corner_radius=0, height=28)
        self.address_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.address_entry.insert(0, self.current_dir)
        self.address_entry.bind("<Return>", self.on_address_enter)
        
        self.btn_change_dir = ctk.CTkButton(self.toolbar, text="Browse", width=80, height=26, 
                                            fg_color=WIN_BG, border_width=1, border_color=WIN_BORDER,
                                            hover_color=WIN_HOVER, text_color=WIN_TEXT, command=self.change_directory,
                                            font=FONT_MAIN, corner_radius=0)
        self.btn_change_dir.pack(side=tk.LEFT, padx=10, pady=12)
        
        # Playback Controls (Loop, Norm, Pause)
        self.loop_var = tk.BooleanVar(value=False)
        self.loop_check = ctk.CTkCheckBox(self.toolbar, text="Loop", width=20, variable=self.loop_var, 
                                          command=self.toggle_loop, font=FONT_MAIN,
                                          text_color=WIN_TEXT, hover_color=WIN_ACCENT, border_color=WIN_MUTED,
                                          fg_color=WIN_ACCENT, checkmark_color=WIN_TEXT, corner_radius=0)
        self.loop_check.pack(side=tk.LEFT, padx=15, pady=12)

        self.norm_var = tk.BooleanVar(value=False)
        self.norm_check = ctk.CTkCheckBox(self.toolbar, text="Normalised", width=20, variable=self.norm_var, 
                                          command=self.toggle_normalization, font=FONT_MAIN,
                                          text_color=WIN_TEXT, hover_color=WIN_ACCENT, border_color=WIN_MUTED,
                                          fg_color=WIN_ACCENT, checkmark_color=WIN_TEXT, corner_radius=0)
        self.norm_check.pack(side=tk.LEFT, padx=15, pady=12)

        self.btn_pause = ctk.CTkButton(self.toolbar, text="Pause", width=80, height=28, 
                                       command=self.toggle_pause_resume, fg_color=WIN_ACCENT, 
                                       hover_color="#1E90FF", text_color=WIN_TEXT, font=FONT_BOLD, corner_radius=0)
        self.btn_pause.pack(side=tk.LEFT, padx=(15, 20), pady=12)
        
        # Progress Bar Section (Status Bar Style)
        self.progress_frame = ctk.CTkFrame(root, height=30, fg_color=WIN_BG, corner_radius=0)
        self.progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.time_label = ctk.CTkLabel(self.progress_frame, text="00:00 / 00:00", font=FONT_MAIN, text_color=WIN_MUTED)
        self.time_label.pack(side=tk.LEFT, padx=15)
        
        self.progress_scale = ctk.CTkSlider(self.progress_frame, from_=0, to=100, command=self.on_slider_move, 
                                            height=16, progress_color=WIN_ACCENT, button_color=WIN_ACCENT, 
                                            button_hover_color=WIN_ACCENT, fg_color=WIN_TOOLBAR, corner_radius=0)
        self.progress_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(15, 25))
        self.progress_scale.set(0)
        self.progress_scale.bind("<ButtonPress-1>", self.on_slider_press)
        self.progress_scale.bind("<ButtonRelease-1>", self.on_slider_release)

        # Track List (File List Style)
        self.scroll_frame = ctk.CTkScrollableFrame(root, fg_color=WIN_BG, corner_radius=0, 
                                                   scrollbar_button_color=WIN_TOOLBAR, 
                                                   scrollbar_button_hover_color=WIN_SELECT)
        self.scroll_frame.pack(pady=0, padx=0, fill=tk.BOTH, expand=True)
        
        self.status_label = ctk.CTkLabel(root, text=" 🟢 Ready", text_color=WIN_MUTED, font=FONT_STATUS)
        self.status_label.pack(side=tk.BOTTOM, anchor="w", padx=15, pady=2)
        
        self.refresh_list()
        
        # Start initial optimization
        start_optimization_worker(self.current_dir, self.on_audio_optimized)
        
        # Periodic Tasks
        self.sync_loop_state()
        self.update_ui_progress()

    def sync_loop_state(self):
        if self.loop_var.get() != state.is_looping:
            self.loop_var.set(state.is_looping)
        if self.norm_var.get() != state.is_normalized:
            self.norm_var.set(state.is_normalized)
        self.root.after(500, self.sync_loop_state)

    def update_ui_progress(self):
        """Updates the slider and time label based on playback state."""
        vc = state.current_voice_client
        if vc and (vc.is_playing() or vc.is_paused()):
            # Update button text based on state
            if vc.is_paused():
                self.btn_pause.configure(text="Play")
            else:
                self.btn_pause.configure(text="Pause")

            if vc.is_playing() and not state.is_seeking:
                current_time = time.time()
                played_seconds = (current_time - state.start_playback_time) + state.elapsed_offset
                
                # Update slider range only if total duration changed
                if state.total_duration > 0:
                    try:
                        if self.progress_scale.cget("to") != state.total_duration:
                            self.progress_scale.configure(to=state.total_duration)
                        self.progress_scale.set(played_seconds)
                        self.time_label.configure(text=f"{format_time(played_seconds)} / {format_time(state.total_duration)}")
                    except Exception:
                        pass
        elif not vc or not vc.is_playing():
             if not state.is_looping:
                self.time_label.configure(text=f"00:00 / {format_time(state.total_duration)}")
                self.progress_scale.set(0)
                self.btn_pause.configure(text="Pause")

        self.root.after(500, self.update_ui_progress)

    def toggle_pause_resume(self):
        """Toggles pause/resume state."""
        vc = state.current_voice_client
        if vc:
            if vc.is_playing():
                asyncio.run_coroutine_threadsafe(pause_logic(), self.bot.loop)
            elif vc.is_paused():
                asyncio.run_coroutine_threadsafe(resume_logic(), self.bot.loop)

    def on_slider_move(self, value):
        # We handle seeking on release to prevent stutter
        pass

    def on_slider_press(self, event):
        state.is_seeking = True

    def on_slider_release(self, event):
        new_seconds = self.progress_scale.get()
        # Update logic immediately before allowing UI updates to resume
        if state.current_track_path:
            # First trigger the audio change
            asyncio.run_coroutine_threadsafe(play_audio_logic(self.bot, state.current_track_path, seek_to=new_seconds), self.bot.loop)
        
        # Short delay to let audio start before resuming UI bar updates
        self.root.after(100, lambda: self.reset_seeking_flag())

    def reset_seeking_flag(self):
        state.is_seeking = False

    def toggle_loop(self):
        state.is_looping = self.loop_var.get()

    def toggle_normalization(self):
        state.is_normalized = self.norm_var.get()

    def refresh_list(self):
        # Clear frame
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        self.track_buttons = {}
        self.file_list = get_audio_files(self.current_dir)
        
        for f in self.file_list:
            status = state.optimized_files.get(f, "Pending")
            status_text = "[Optimised]" if status is True else "[Pending]"
            status_color = WIN_GREEN if status is True else WIN_MUTED
            
            btn = ctk.CTkButton(self.scroll_frame, 
                                text=f"   📄  {f}   ({status_text})", 
                                anchor="w",
                                fg_color="transparent",
                                text_color=WIN_TEXT,
                                hover_color=WIN_HOVER,
                                height=30,
                                font=FONT_MAIN,
                                corner_radius=0,
                                command=lambda fname=f: self.play_track(fname))
            btn.pack(fill=tk.X, pady=0, padx=0) # Flush list
            self.track_buttons[f] = btn
            
        # Update address bar
        self.address_entry.delete(0, tk.END)
        self.address_entry.insert(0, self.current_dir)

    def play_track(self, filename):
        """Called when a track button is clicked."""
        filepath = os.path.join(self.current_dir, filename)
        asyncio.run_coroutine_threadsafe(play_audio_logic(self.bot, filepath), self.bot.loop)

    def on_audio_optimized(self, filename, is_optimized):
        """Callback from the optimization worker."""
        if filename in self.track_buttons:
            status_text = "[Optimised]" if is_optimized else "[Pending]"
            # schedule this on the main thread
            self.root.after(0, lambda: self.track_buttons[filename].configure(
                text=f"   📄  {filename}   ({status_text})"
            ))

    def change_directory(self):
        new_dir = filedialog.askdirectory(initialdir=self.current_dir, title="Select Music Folder")
        if new_dir:
            self.current_dir = new_dir
            # Reset state for new folder
            state.optimized_files = {}
            self.refresh_list()
            start_optimization_worker(self.current_dir, self.on_audio_optimized)

    def on_address_enter(self, event=None):
        """Called when Enter is pressed in the address bar."""
        new_path = self.address_entry.get().strip()
        if os.path.isdir(new_path):
            self.current_dir = new_path
            state.optimized_files = {}
            self.refresh_list()
            start_optimization_worker(self.current_dir, self.on_audio_optimized)
        else:
            # Revert to current valid path
            self.address_entry.delete(0, tk.END)
            self.address_entry.insert(0, self.current_dir)
            # Subtle status update
            self.status_label.configure(text=" ⚠️  Invalid Path", text_color=WIN_WARNING)
            self.root.after(2000, lambda: self.status_label.configure(text=" 🟢 Ready", text_color=WIN_MUTED))
