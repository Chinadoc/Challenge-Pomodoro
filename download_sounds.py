#!/usr/bin/env python3
"""
Download sound files for the Pomodoro Timer application.
This script downloads free sound files from GitHub and saves them to the sounds/default directory.
"""

import os
import urllib.request
import ssl
import shutil
import subprocess

# Base URL for sound files (using a GitHub repository with free sound files)
SOUNDS_BASE_URL = "https://github.com/chrislopez28/pomodoro-sounds/raw/main/"

# Sound file mapping - filename: URL path
SOUND_FILES = {
    "work_start.wav": "bell/bell_start.wav",
    "work_end.wav": "bell/bell_end.wav",
    "break_start.wav": "bell/bell_break_start.wav",
    "break_end.wav": "bell/bell_break_end.wav",
    "pause.wav": "ui/pause.wav",
    "resume.wav": "ui/resume.wav",
    "reset.wav": "ui/reset.wav",
    "notification.wav": "notification/notification.wav"
}

# Alternative URLs if the primary ones fail
ALTERNATIVE_URLS = {
    "work_start.wav": "https://github.com/freeCodeCamp/freeCodeCamp/raw/main/client/static/sounds/timer/alarm1.mp3",
    "work_end.wav": "https://github.com/freeCodeCamp/freeCodeCamp/raw/main/client/static/sounds/timer/alarm2.mp3",
    "break_start.wav": "https://github.com/freeCodeCamp/freeCodeCamp/raw/main/client/static/sounds/timer/notification1.mp3",
    "break_end.wav": "https://github.com/freeCodeCamp/freeCodeCamp/raw/main/client/static/sounds/timer/notification2.mp3",
    "pause.wav": "https://github.com/freeCodeCamp/freeCodeCamp/raw/main/client/static/sounds/timer/click1.mp3",
    "resume.wav": "https://github.com/freeCodeCamp/freeCodeCamp/raw/main/client/static/sounds/timer/click2.mp3",
    "reset.wav": "https://github.com/freeCodeCamp/freeCodeCamp/raw/main/client/static/sounds/timer/click3.mp3",
    "notification.wav": "https://github.com/freeCodeCamp/freeCodeCamp/raw/main/client/static/sounds/timer/alarm3.mp3"
}

def download_file(url, target_path):
    """Download a file from a URL to a target path."""
    try:
        # Create an SSL context that doesn't verify certificates
        # This is needed because some URLs might have SSL certificate issues
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        # Download the file
        with urllib.request.urlopen(url, context=ctx) as response, open(target_path, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def convert_mp3_to_wav(mp3_path, wav_path):
    """Convert an MP3 file to WAV using ffmpeg if available, otherwise keep as MP3."""
    try:
        # Check if ffmpeg is installed
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        
        # Convert using ffmpeg
        subprocess.run([
            "ffmpeg", "-i", mp3_path, "-acodec", "pcm_s16le", "-ar", "44100", wav_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        
        # Remove the original MP3 file
        os.remove(mp3_path)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print("ffmpeg not found or conversion failed. Keeping MP3 file and renaming to .wav")
        # Just rename the file if ffmpeg is not available
        os.rename(mp3_path, wav_path)
        return True
    except Exception as e:
        print(f"Error converting {mp3_path} to WAV: {e}")
        return False

def main():
    """Main function to download all sound files."""
    # Define the target directory
    target_dir = os.path.join(os.path.dirname(__file__), "sounds", "default")
    
    # Create the directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)
    
    successful_downloads = 0
    
    for filename, path in SOUND_FILES.items():
        target_path = os.path.join(target_dir, filename)
        url = SOUNDS_BASE_URL + path
        
        print(f"Downloading {filename}...")
        
        # Try the primary URL
        if download_file(url, target_path):
            successful_downloads += 1
            print(f"✓ Successfully downloaded {filename}")
        else:
            # Try the alternative URL if primary fails
            alt_url = ALTERNATIVE_URLS.get(filename)
            if alt_url:
                print(f"Trying alternative source for {filename}...")
                
                # For MP3 files, we need to download and convert
                if alt_url.endswith(".mp3"):
                    temp_path = target_path.replace(".wav", ".mp3")
                    if download_file(alt_url, temp_path):
                        if convert_mp3_to_wav(temp_path, target_path):
                            successful_downloads += 1
                            print(f"✓ Successfully downloaded and converted {filename}")
                else:
                    if download_file(alt_url, target_path):
                        successful_downloads += 1
                        print(f"✓ Successfully downloaded {filename} from alternative source")
    
    print(f"\nDownload complete: {successful_downloads}/{len(SOUND_FILES)} files downloaded successfully.")
    if successful_downloads == len(SOUND_FILES):
        print("All sound files have been downloaded. Your Pomodoro Timer should now have working sounds!")
    else:
        print(f"Some files could not be downloaded. The Pomodoro Timer will use the {successful_downloads} available sounds.")

if __name__ == "__main__":
    main()
