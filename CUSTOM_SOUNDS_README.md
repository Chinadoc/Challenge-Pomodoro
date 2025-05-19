# Custom Sounds for Pomodoro Timer

This guide explains how to set up and use custom ElevenLabs voice prompts with your Pomodoro Timer.

## Prerequisites

1. Python 3.6 or higher
2. An ElevenLabs API key (get one at [https://elevenlabs.io/](https://elevenlabs.io/))
3. Required Python packages: `requests`

## Setup Instructions

1. **Install required packages**:
   ```bash
   pip install requests
   ```

2. **Set your ElevenLabs API key** as an environment variable:
   ```bash
   # On macOS/Linux
   export ELEVENLABS_API_KEY='your-api-key-here'
   
   # On Windows
   set ELEVENLABS_API_KEY=your-api-key-here
   ```

3. **Set up the sound pack** (creates necessary directories and config):
   ```bash
   python setup_sound_pack.py
   ```

4. **Generate the voice prompts**:
   ```bash
   python generate_elevenlabs_sounds.py
   ```
   This will create MP3 files in the `sounds/elevenlabs` directory.

5. **Restart the Pomodoro Timer** to use the new sounds.

## Customizing the Prompts

Edit the `SOUND_PROMPTS` dictionary in `generate_elevenlabs_sounds.py` to change:
- The spoken text
- Voice characteristics (stability, similarity_boost, etc.)
- Add or remove sound events

## Available Sound Events

- `work_start`: Played when a work session starts
- `work_end`: Played when a work session ends
- `break_start`: Played when a break starts
- `break_end`: Played when a break ends
- `pause`: Played when the timer is paused
- `resume`: Played when the timer is resumed
- `notification`: General notification sound
- `achievement`: Played when an achievement is unlocked

## Troubleshooting

- **No sound?** Check that:
  - The sound files are in the correct directory (`sounds/elevenlabs/`)
  - The filenames in `config.json` match the generated MP3 files
  - Your system volume is up and not muted
  - The Pomodoro Timer has sound enabled in its settings

- **API Errors?**
  - Verify your ElevenLabs API key is set correctly
  - Check your internet connection
  - Make sure you have sufficient credits in your ElevenLabs account

## License

These scripts are provided as-is under the MIT License. The generated voice prompts are subject to ElevenLabs' terms of service.
