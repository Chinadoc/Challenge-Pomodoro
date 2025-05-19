#!/usr/bin/env python3
"""
Generate custom sound effects for the Pomodoro Timer using ElevenLabs API.
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

# API Endpoint - Updated to the correct endpoint
API_URL = "https://api.elevenlabs.io/v1/sound-generation"

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "sounds", "elevenlabs_sfx")

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Sound effects configuration - Cosmic Evolution Themed Pomodoro Timer
SOUND_EFFECTS = {
    "work_start": {
        "text": "A gentle rising tone followed by a warm voice saying 'Focus begins now' against a backdrop of subtle cosmic particles forming. The voice sounds positive and encouraging, with a hint of cosmic resonance.",
        "duration_seconds": 2.0,
        "prompt_influence": 0.7
    },
    "work_end": {
        "text": "A satisfying completion sound with a warm voice saying 'Well done' followed by the sound of stellar formation. The voice conveys genuine accomplishment, like witnessing the birth of a star.",
        "duration_seconds": 2.5,
        "prompt_influence": 0.7
    },
    "break_start": {
        "text": "A relaxing sound of cosmic wind with a soothing voice saying 'Time to rest'. The voice has a calming quality like floating peacefully through space, with subtle nebula sounds in the background.",
        "duration_seconds": 2.5,
        "prompt_influence": 0.6
    },
    "break_end": {
        "text": "A gentle cosmic pulse followed by an encouraging voice saying 'Let's continue the journey'. The voice has a motivating quality that suggests returning to productive orbit.",
        "duration_seconds": 2.0,
        "prompt_influence": 0.6
    },
    "pause": {
        "text": "A soft 'Pausing for a moment' with a calm voice that suggests time is temporarily suspended, like a cosmic pause. The voice is understanding and brief, with a subtle suspension chord.",
        "duration_seconds": 1.5,
        "prompt_influence": 0.7
    },
    "resume": {
        "text": "A confident 'Back to it' with a slight forward momentum, like a planet resuming its orbit. The voice has an upbeat quality suggesting reengagement with productive flow.",
        "duration_seconds": 1.5,
        "prompt_influence": 0.7
    },
    "notification": {
        "text": "A clean, cosmic ping like a distant star sending a signal. The sound is clear but not intrusive, perfect for an alert in space.",
        "duration_seconds": 1.0,
        "prompt_influence": 0.6
    },
    "achievement": {
        "text": "An exciting cosmic fanfare with a congratulatory voice announcing 'Achievement unlocked!'. The sound suggests a celestial discovery, with distant stars twinkling and subtle cosmic celebration sounds.",
        "duration_seconds": 3.0,
        "prompt_influence": 0.8
    },
    "rank_up": {
        "text": "A progressive ascending cosmic tone sequence followed by an impressed voice saying 'Cosmic evolution! You've reached a new level of productivity'. The sound suggests expanding into a more advanced celestial body, with building energy and distant applause.",
        "duration_seconds": 3.5,
        "prompt_influence": 0.8
    }
}

def generate_sound_effect(sound_name, config):
    """Generate a sound effect using ElevenLabs Sound Generation API."""
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Build payload according to the API documentation
    payload = {
        "text": config["text"],
        "duration_seconds": config["duration_seconds"],
        "prompt_influence": config["prompt_influence"]
    }
    
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

These sound effects were generated using ElevenLabs Sound Generation API on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

To use these sounds in the Pomodoro Timer:
1. Copy these files to your Pomodoro Timer's sounds directory
2. In the app settings, select the appropriate sound for each event

Sound files:
""")
        for sound in SOUND_EFFECTS.keys():
            f.write(f"- {sound}.mp3\n")

if __name__ == "__main__":
    main()
