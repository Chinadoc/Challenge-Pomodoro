#!/usr/bin/env python3
"""
Generate simple sound files for the Pomodoro Timer application.
This script uses pygame to create .wav files for various timer events.
"""

import os
import pygame
import numpy as np
import time

def generate_tone(frequency, duration, volume=0.5, sample_rate=44100):
    """Generate a sine wave at the specified frequency."""
    # Calculate the number of samples
    n_samples = int(duration * sample_rate)
    
    # Generate time array
    t = np.linspace(0, duration, n_samples, False)
    
    # Generate sine wave
    tone = np.sin(frequency * 2 * np.pi * t) * volume
    
    # Ensure the sound fades in/out
    fade = 0.1  # seconds to fade
    fade_samples = int(fade * sample_rate)
    
    # Apply fade in
    if fade_samples > 0:
        fade_in = np.linspace(0, 1, fade_samples)
        tone[:fade_samples] *= fade_in
    
    # Apply fade out
    if fade_samples > 0 and fade_samples < n_samples:
        fade_out = np.linspace(1, 0, fade_samples)
        tone[-fade_samples:] *= fade_out
    
    # Convert to 16-bit data
    audio = (tone * 32767).astype(np.int16)
    
    return audio

def save_sound(audio_data, filename, sample_rate=44100):
    """Save the audio data to a WAV file."""
    pygame.mixer.quit()  # Ensure mixer is closed before writing files
    
    # Initialize pygame
    pygame.mixer.init(frequency=sample_rate, size=-16, channels=1)
    
    # Create a Sound object
    sound = pygame.sndarray.make_sound(audio_data)
    
    # Save the sound to a file
    pygame.sndarray.save(sound, filename)
    
    # Clean up
    pygame.mixer.quit()

def main():
    """Main function to generate and save all sound files."""
    # Define the target directory
    target_dir = os.path.join(os.path.dirname(__file__), "sounds", "default")
    
    # Create the directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)
    
    # Sound configuration
    sounds = {
        "work_start.wav": {"freq": 440, "duration": 0.6},  # A4 note
        "work_end.wav": {"freq": 523, "duration": 0.8},    # C5 note
        "break_start.wav": {"freq": 587, "duration": 0.6}, # D5 note
        "break_end.wav": {"freq": 659, "duration": 0.8},   # E5 note
        "pause.wav": {"freq": 784, "duration": 0.2},       # G5 note, short
        "resume.wav": {"freq": 880, "duration": 0.3},      # A5 note, short
        "reset.wav": {"freq": 698, "duration": 0.5},       # F5 note, medium
        "notification.wav": {"freq": 988, "duration": 0.7}, # B5 note
    }
    
    for filename, config in sounds.items():
        print(f"Generating {filename}...")
        
        # Generate tone
        audio_data = generate_tone(
            frequency=config["freq"],
            duration=config["duration"],
            volume=0.6,
        )
        
        # Save to file
        filepath = os.path.join(target_dir, filename)
        save_sound(audio_data, filepath)
        
        # Small delay to allow file to be written
        time.sleep(0.1)
        
        if os.path.exists(filepath):
            print(f"✓ Successfully created {filename}")
        else:
            print(f"✗ Failed to create {filename}")
    
    print("\nSound generation complete!")
    print("Your Pomodoro Timer should now have working sounds.")

if __name__ == "__main__":
    pygame.init()
    main()
    pygame.quit()
