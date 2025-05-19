import os
import requests
from dotenv import load_dotenv
import json
from pathlib import Path

# Load environment variables
load_dotenv()

# Configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Default voice ID (Rachel)
OUTPUT_DIR = Path("assets/sounds/achievements")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Achievement sounds configuration
ACHIEVEMENT_SOUNDS = {
    "early_bird": {
        "text": "Early bird gets the worm! You've earned the Early Bird achievement by starting your day strong.",
        "stability": 0.5,
        "similarity_boost": 0.8
    },
    "marathoner": {
        "text": "Incredible stamina! You've completed a marathon of pomodoros and earned the Marathoner achievement.",
        "stability": 0.6,
        "similarity_boost": 0.85
    },
    "weekend_warrior": {
        "text": "Weekend warrior! Your dedication on the weekend has earned you this special achievement.",
        "stability": 0.55,
        "similarity_boost": 0.8
    },
    "night_owl": {
        "text": "The night is still young! You've earned the Night Owl achievement for burning the midnight oil.",
        "stability": 0.5,
        "similarity_boost": 0.75,
        "voice_id": "MF3mGyEYCl7XYWbV9V6O"  # Different voice for night owl
    },
    "perfect_week": {
        "text": "Flawless victory! A perfect week of productivity earns you this achievement.",
        "stability": 0.7,
        "similarity_boost": 0.9
    },
    "focused_mind": {
        "text": "Laser focus! Your ability to concentrate has unlocked the Focused Mind achievement.",
        "stability": 0.6,
        "similarity_boost": 0.85
    },
    "quick_draw": {
        "text": "Quick on the draw! You've earned this achievement for your lightning-fast work transitions.",
        "stability": 0.65,
        "similarity_boost": 0.9
    },
    "balanced": {
        "text": "Perfect balance! You've mastered the art of work-life balance with this achievement.",
        "stability": 0.5,
        "similarity_boost": 0.8
    },
    "early_riser": {
        "text": "Rise and shine! Your early morning productivity has earned you the Early Riser achievement.",
        "stability": 0.55,
        "similarity_boost": 0.85
    },
    "power_hour": {
        "text": "Power hour complete! You've earned this achievement for an hour of focused productivity.",
        "stability": 0.7,
        "similarity_boost": 0.9,
        "voice_id": "GBv7mTt0atIp3Br8iCZE"  # Different voice for power hour
    }
}

def generate_sound(achievement_id, config):
    """Generate a sound file using ElevenLabs API"""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{config.get('voice_id', VOICE_ID)}"
    
    headers = {
        "Accept": "audio/mpeg",
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    data = {
        "text": config["text"],
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": config["stability"],
            "similarity_boost": config["similarity_boost"]
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        output_file = OUTPUT_DIR / f"{achievement_id}.mp3"
        with open(output_file, 'wb') as f:
            f.write(response.content)
            
        print(f"✅ Generated {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error generating {achievement_id}: {str(e)}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Error details: {e.response.text}")
        return False

def main():
    if not ELEVENLABS_API_KEY:
        print("❌ Error: ELEVENLABS_API_KEY not found in .env file")
        return
    
    print("Starting achievement sound generation...")
    
    success_count = 0
    for achievement_id, config in ACHIEVEMENT_SOUNDS.items():
        output_file = OUTPUT_DIR / f"{achievement_id}.mp3"
        if output_file.exists():
            print(f"ℹ️  {output_file} already exists, skipping.")
            success_count += 1
            continue
            
        if generate_sound(achievement_id, config):
            success_count += 1
    
    print(f"\n🎉 Successfully generated {success_count}/{len(ACHIEVEMENT_SOUNDS)} achievement sounds!")

if __name__ == "__main__":
    main()
