#!/usr/bin/env python3
"""
Generate custom sound effects for the Pomodoro Timer using ElevenLabs Sound Effects API.
This script creates various sound effects for different timer events.
"""

import os
import requests
import json
from pathlib import Path
from datetime import datetime
import time

# Configuration
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
if not ELEVENLABS_API_KEY:
    raise ValueError("Please set the ELEVENLABS_API_KEY environment variable")

# API Endpoint
API_URL = "https://api.elevenlabs.io/v1/sound-effects/generate"

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "sounds", "sfx")

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Sound effects configuration - Pomodoro Timer
SOUND_EFFECTS = {
    # Work Session Start - Decisive, attention-grabbing ping
    "work_start": {
        "description": "A crisp, bright ping that signals the start of focused work time",
        "category": "ping",
        "intensity": 0.7,
        "duration": 1.0,
        "pitch_variation": 0.4,
        "pitch_shift": 0.2  # Slight upward inflection
    },
    
    # Work Session End - Resolving, satisfying chime
    "work_end": {
        "description": "A resolving two-note chime that provides closure to the work session",
        "category": "chime",
        "intensity": 0.75,
        "duration": 1.8,
        "pitch_variation": 0.3,
        "pitch_shift": -0.15  # Slight downward resolution
    },
    
    # Break Start - Light, airy transition
    "break_start": {
        "description": "A light, airy wind chime that signals the start of break time",
        "category": "chime",
        "intensity": 0.5,
        "duration": 2.2,
        "pitch_variation": 0.6,
        "pitch_shift": -0.2  # Gentle descent
    },
    
    # Break End - Gentle but attention-grabbing
    "break_end": {
        "description": "A gentle but noticeable ping to signal the end of break time",
        "category": "ping",
        "intensity": 0.65,
        "duration": 1.0,
        "pitch_variation": 0.3,
        "pitch_shift": 0.15  # Slight upward inflection
    },
    
    # Pause - Subtle, muted click
    "pause": {
        "description": "A soft, muted click sound for pausing the timer",
        "category": "click",
        "intensity": 0.4,
        "duration": 0.4,
        "pitch_variation": 0.1,
        "pitch_shift": -0.1  # Slightly lower pitch
    },
    
    # Resume - Slightly brighter than pause
    "resume": {
        "description": "A subtle ping with slight upward inflection for resuming the timer",
        "category": "ping",
        "intensity": 0.45,
        "duration": 0.45,
        "pitch_variation": 0.15,
        "pitch_shift": 0.1  # Slightly higher than pause
    },
    
    # Notification - Clean, neutral alert
    "notification": {
        "description": "A clean, neutral blip for general notifications",
        "category": "ping",
        "intensity": 0.6,
        "duration": 0.8,
        "pitch_variation": 0.2,
        "pitch_shift": 0.0  # Neutral pitch
    },
    
    # Achievement - Celebratory but not overwhelming
    "achievement": {
        "description": "A bright, celebratory chime sequence for achievements",
        "category": "chime",
        "intensity": 0.8,
        "duration": 2.5,
        "pitch_variation": 0.7,
        "pitch_shift": 0.3  # Upward, celebratory
    }
}

def generate_sound_effect(sound_name, config):
    """Generate a sound effect using ElevenLabs Sound Effects API."""
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Build payload with all available parameters
    payload = {
        "description": config["description"],
        "category": config["category"],
        "intensity": config["intensity"],
        "duration": config["duration"],
        "pitch_variation": config["pitch_variation"],
        "output_format": "mp3"
    }
    
    # Add pitch_shift if specified
    if "pitch_shift" in config:
        payload["pitch_shift"] = config["pitch_shift"]
    
    print(f"Generating {sound_name} sound effect...")
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        response.raise_for_status()
        
        # Save the sound effect
        output_file = os.path.join(OUTPUT_DIR, f"{sound_name}.mp3")
        
        with open(output_file, 'wb') as f:
            f.write(response.content)
        
        print(f"✓ Successfully created {output_file}")
        return True
    except Exception as e:
        print(f"✗ Error generating {sound_name}: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False

def main():
    print("Starting sound effects generation with ElevenLabs...\n")
    
    # Generate each sound effect
    success_count = 0
    for sound_name, config in SOUND_EFFECTS.items():
        if generate_sound_effect(sound_name, config):
            success_count += 1
        time.sleep(1)  # Rate limiting
    
    print(f"\nSound effects generation complete! {success_count}/{len(SOUND_EFFECTS)} sounds generated.")
    print(f"Sounds saved to: {os.path.abspath(OUTPUT_DIR)}")
    
    # Create a README file with instructions
    readme_path = os.path.join(OUTPUT_DIR, "README.txt")
    with open(readme_path, 'w') as f:
        f.write(f"""Pomodoro Timer Sound Effects
================================

These sound effects were generated using ElevenLabs Sound Effects API on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

To use these sounds in the Pomodoro Timer:
1. Copy these files to your Pomodoro Timer's sounds directory
2. In the app settings, select the appropriate sound for each event

Sound files:
""")
        for sound in SOUND_EFFECTS.keys():
            f.write(f"- {sound}.mp3\n")

if __name__ == "__main__":
    main()
