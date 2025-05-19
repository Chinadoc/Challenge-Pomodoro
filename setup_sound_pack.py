#!/usr/bin/env python3
"""
Set up the sound pack configuration for the Pomodoro Timer.
This creates the necessary directory structure and configuration file.
"""

import os
import json
import shutil
from pathlib import Path

# Configuration
SOUND_PACK_NAME = "elevenlabs"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "pomodoro-timer")
CONFIG_FILE = os.path.join(CONFIG_DIR, "sound_pack.json")

# Sound pack configuration
SOUND_PACK_CONFIG = {
    "name": "ElevenLabs Voice Pack",
    "version": "1.0.0",
    "author": "Custom Generated",
    "description": "Natural-sounding voice prompts generated with ElevenLabs API",
    "sounds": {
        "work_start": "work_start.mp3",
        "work_end": "work_end.mp3",
        "break_start": "break_start.mp3",
        "break_end": "break_end.mp3",
        "pause": "pause.mp3",
        "resume": "resume.mp3",
        "notification": "notification.mp3",
        "achievement": "achievement.mp3"
    }
}

def create_sound_pack():
    """Create the sound pack directory and configuration."""
    # Create the sound pack directory
    sound_pack_dir = os.path.join(os.path.dirname(__file__), "sounds", SOUND_PACK_NAME)
    os.makedirs(sound_pack_dir, exist_ok=True)
    
    # Create the config directory if it doesn't exist
    os.makedirs(CONFIG_DIR, exist_ok=True)
    
    # Save the sound pack configuration
    config_path = os.path.join(sound_pack_dir, "config.json")
    with open(config_path, 'w') as f:
        json.dump(SOUND_PACK_CONFIG, f, indent=2)
    
    # Update the main config to use this sound pack
    main_config_path = os.path.join(CONFIG_DIR, "config.json")
    if os.path.exists(main_config_path):
        with open(main_config_path, 'r') as f:
            config = json.load(f)
    else:
        config = {}
    
    config["sound_pack"] = SOUND_PACK_NAME
    
    with open(main_config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✓ Sound pack '{SOUND_PACK_NAME}' has been set up successfully!")
    print(f"  - Sound files directory: {os.path.abspath(sound_pack_dir)}")
    print(f"  - Configuration saved to: {os.path.abspath(config_path)}")
    print("\nNext steps:")
    print(f"1. Run 'python generate_elevenlabs_sounds.py' to generate the voice prompts")
    print(f"2. Move the generated MP3 files to: {os.path.abspath(sound_pack_dir)}")
    print(f"3. Restart the Pomodoro Timer to use the new sounds")

if __name__ == "__main__":
    create_sound_pack()
