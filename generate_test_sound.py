import os
import numpy as np
from scipy.io import wavfile

def generate_beep(filename, duration=0.1, frequency=440, sample_rate=44100):
    """Generate a simple beep sound."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(2 * np.pi * frequency * t) * 0.5  # 0.5 volume
    
    # Convert to 16-bit data
    audio = (tone * 32767).astype(np.int16)
    
    # Save as WAV file
    wavfile.write(filename, sample_rate, audio)
    print(f"Generated test sound: {filename}")

# Create sounds directory if it doesn't exist
os.makedirs('sounds/classic', exist_ok=True)

# Generate test sounds
generate_beep('sounds/classic/work_start.wav', 0.2, 440)  # A4 note
generate_beep('sounds/classic/work_end.wav', 0.5, 554.37)  # C#5 note
generate_beep('sounds/classic/break_start.wav', 0.2, 523.25)  # C5 note
generate_beep('sounds/classic/break_end.wav', 0.5, 659.25)  # E5 note
generate_beep('sounds/classic/notification.wav', 0.1, 880)  # A5 note
generate_beep('sounds/classic/pause.wav', 0.1, 440)  # A4 note
generate_beep('sounds/classic/resume.wav', 0.1, 523.25)  # C5 note
generate_beep('sounds/classic/achievement.wav', 1.0, 880, 22050)  # A5 note, longer duration

print("Test sounds generated in sounds/classic/")
