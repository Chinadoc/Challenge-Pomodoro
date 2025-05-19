#!/usr/bin/env python3
"""
Generate professional sound effects for the Pomodoro Timer.
This script creates synthetic sounds that match our design specifications.
"""

import os
import numpy as np
from pydub import AudioSegment
from pydub.generators import Sine, Square, Pulse, WhiteNoise
from pydub.effects import low_pass_filter, high_pass_filter
import math

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "sounds", "sfx")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Sample rate and bit depth
SAMPLE_RATE = 44100
BIT_DEPTH = 16

# Base frequency (A4)
BASE_FREQ = 440

def generate_tone(freq, duration, volume=0.5, wave_type='sine', decay=0.5):
    """Generate a tone with optional decay."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), False)
    
    if wave_type == 'sine':
        tone = np.sin(2 * np.pi * freq * t)
    elif wave_type == 'square':
        tone = np.sign(np.sin(2 * np.pi * freq * t))
    elif wave_type == 'sawtooth':
        tone = 2 * (t * freq - np.floor(0.5 + t * freq))
    else:  # triangle
        tone = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5)))
    
    # Apply volume
    tone = tone * volume
    
    # Apply decay
    if decay > 0:
        decay_env = np.exp(-decay * t)
        tone = tone * decay_env
    
    # Convert to 16-bit data
    audio = (tone * 32767).astype(np.int16)
    
    # Create AudioSegment
    sound = AudioSegment(
        audio.tobytes(),
        frame_rate=SAMPLE_RATE,
        sample_width=2,  # 16-bit
        channels=1
    )
    
    return sound

def create_work_start():
    """Create a crisp, bright ping for work start."""
    # Main ping sound (high frequency sine wave with quick decay)
    ping = generate_tone(1200, 0.4, 0.7, 'sine', 8)
    
    # Add a subtle attack at the beginning
    attack = generate_tone(2000, 0.05, 0.3, 'sine', 20)
    sound = attack.overlay(ping, position=0)
    
    # Apply a quick fade out
    sound = sound.fade_out(100)
    
    # Normalize
    sound = sound.apply_gain(-sound.dBFS + 6)
    
    return sound

def create_work_end():
    """Create a resolving two-note chime for work end."""
    # First note (A4)
    note1 = generate_tone(440, 0.6, 0.6, 'sine', 2)
    # Second note (E4) - lower and slightly quieter
    note2 = generate_tone(330, 1.2, 0.5, 'sine', 1.5)
    
    # Overlay the notes with a slight delay
    sound = note1.overlay(note2, position=200)  # 200ms delay
    
    # Apply fade out
    sound = sound.fade_out(300)
    
    # Apply a gentle low-pass filter
    sound = low_pass_filter(sound, 2000)
    
    return sound

def create_break_start():
    """Create a light, airy wind chime for break start."""
    # Create multiple sine waves at different frequencies
    base_freq = 600
    sounds = []
    
    for i in range(3):
        freq = base_freq * (i + 1) * 0.8
        duration = 1.5 + (i * 0.2)
        decay = 1.5 - (i * 0.3)
        tone = generate_tone(freq, duration, 0.4, 'sine', decay)
        sounds.append(tone)
    
    # Mix the sounds
    sound = sounds[0]
    for s in sounds[1:]:
        sound = sound.overlay(s, position=0)
    
    # Apply a band-pass filter for wind chime effect
    sound = high_pass_filter(sound, 500)
    sound = low_pass_filter(sound, 3000)
    
    # Add some reverb (simulated with a quiet echo)
    echo = sound - 12  # 12dB quieter
    sound = sound.overlay(echo, position=50)
    
    return sound

def create_break_end():
    """Create a gentle but noticeable ping for break end."""
    # Main ping sound
    ping = generate_tone(1000, 0.3, 0.6, 'sine', 6)
    
    # Add a subtle lower octave
    ping_low = generate_tone(500, 0.4, 0.3, 'sine', 4)
    sound = ping.overlay(ping_low, position=0)
    
    # Apply a quick fade out
    sound = sound.fade_out(100)
    
    return sound

def create_pause():
    """Create a subtle click for pause."""
    # Very short click sound
    click = generate_tone(1200, 0.05, 0.4, 'square', 40)
    
    # Apply a quick low-pass filter
    sound = low_pass_filter(click, 2000)
    
    return sound

def create_resume():
    """Create a slightly brighter ping for resume."""
    # Similar to pause but slightly higher pitch and brighter
    ping = generate_tone(1500, 0.1, 0.45, 'sine', 30)
    
    # Add a subtle attack
    attack = generate_tone(2000, 0.02, 0.3, 'sine', 50)
    sound = attack.overlay(ping, position=0)
    
    return sound

def create_notification():
    """Create a clean, neutral blip for notifications."""
    # Simple sine wave with medium decay
    blip = generate_tone(800, 0.3, 0.6, 'sine', 8)
    
    # Apply a quick fade out
    sound = blip.fade_out(100)
    
    return sound

def create_achievement():
    """Create a celebratory chime sequence for achievements."""
    # Create a sequence of notes (C major arpeggio)
    notes = [
        (523.25, 0.2, 0.6),  # C5
        (659.25, 0.2, 0.6),  # E5
        (783.99, 0.2, 0.6),  # G5
        (1046.5, 0.5, 0.7)   # C6
    ]
    
    # Generate each note
    sounds = []
    for i, (freq, duration, volume) in enumerate(notes):
        note = generate_tone(freq, duration, volume, 'sine', 2)
        sounds.append((note, i * 150))  # 150ms between notes
    
    # Create a silent segment to overlay the notes on
    total_duration = sum(d for _, d, _ in notes) * 1000  # in ms
    sound = AudioSegment.silent(duration=total_duration)
    
    # Overlay each note at the correct position
    for note, position in sounds:
        sound = sound.overlay(note, position=position)
    
    # Apply a gentle fade out
    sound = sound.fade_out(200)
    
    # Add some sparkle with a high-frequency layer
    sparkle = generate_tone(3000, 1.0, 0.3, 'sine', 4)
    sound = sound.overlay(sparkle, position=0)
    
    return sound

def save_sound(sound, filename):
    """Save the sound to a file."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    sound.export(filepath, format="mp3", bitrate="192k")
    print(f"✓ Created {filename}")

def main():
    print("Generating professional sound effects...\n")
    
    # Generate and save all sounds
    sounds = [
        ("work_start.mp3", create_work_start()),
        ("work_end.mp3", create_work_end()),
        ("break_start.mp3", create_break_start()),
        ("break_end.mp3", create_break_end()),
        ("pause.mp3", create_pause()),
        ("resume.mp3", create_resume()),
        ("notification.mp3", create_notification()),
        ("achievement.mp3", create_achievement())
    ]
    
    for filename, sound in sounds:
        save_sound(sound, filename)
    
    print("\n✓ All sounds generated successfully!")
    print(f"Sounds saved to: {os.path.abspath(OUTPUT_DIR)}")
    print("\nTo use these sounds in your Pomodoro Timer:")
    print("1. Open the app settings")
    print("2. Navigate to the Sound settings")
    print("3. Select the corresponding sound file for each event")
    print("4. Save your settings")

if __name__ == "__main__":
    # Install required packages if not already installed
    try:
        import pydub
        import numpy as np
    except ImportError:
        print("Installing required packages...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pydub", "numpy"])
    
    main()
