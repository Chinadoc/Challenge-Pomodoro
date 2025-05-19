#!/usr/bin/env python3
"""
Simple sound generator for Pomodoro Timer using Python's wave module
"""

import os
import math
import wave
import struct


def generate_sine_wave(frequency=440.0, duration=1.0, volume=0.5, sample_rate=44100):
    """Generate a sine wave with the given parameters"""
    # Calculate total number of frames
    n_frames = int(duration * sample_rate)
    
    # Create frames as an array of bytes
    frames = bytearray()
    fade_samples = int(0.1 * n_frames)
    
    for i in range(n_frames):
        # Calculate value for sine wave
        value = volume * math.sin(2 * math.pi * frequency * i / sample_rate)
        # Apply fade in
        if i < fade_samples:
            value *= (i / fade_samples)
        # Apply fade out
        elif i > n_frames - fade_samples:
            value *= ((n_frames - i) / fade_samples)
        # Pack into 16-bit signed
        frames.extend(struct.pack('<h', int(value * 32767)))
    
    return frames


def save_wav(filename, frames, sample_rate=44100):
    """Save frames to a WAV file"""
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)  # mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(frames)


def main():
    sound_dir = os.path.join(os.path.dirname(__file__), 'sounds', 'default')
    os.makedirs(sound_dir, exist_ok=True)

    sounds = {
        'work_start.wav': {'freq': 440, 'duration': 0.6},
        'work_end.wav': {'freq': 523, 'duration': 0.8},
        'break_start.wav': {'freq': 587, 'duration': 0.6},
        'break_end.wav': {'freq': 659, 'duration': 0.8},
        'pause.wav': {'freq': 784, 'duration': 0.2},
        'resume.wav': {'freq': 880, 'duration': 0.3},
        'reset.wav': {'freq': 698, 'duration': 0.5},
        'notification.wav': {'freq': 988, 'duration': 0.7},
    }

    for name, cfg in sounds.items():
        print(f"Generating {name}...")
        frames = generate_sine_wave(
            frequency=cfg['freq'],
            duration=cfg['duration'],
            volume=0.6
        )
        path = os.path.join(sound_dir, name)
        save_wav(path, frames)
        print(f"✓ Saved {name} to {path}")

    print("\nSound generation complete!")


if __name__ == '__main__':
    main()
