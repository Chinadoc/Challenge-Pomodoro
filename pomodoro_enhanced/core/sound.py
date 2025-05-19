"""
Sound management for the Enhanced Pomodoro Timer.
Handles playing sound effects and managing audio settings.
"""

import os
import logging
import platform
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Union, Callable
from dataclasses import dataclass

# Try to import sound-related libraries
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

# Initialize logger
logger = logging.getLogger(__name__)

@dataclass
class SoundEffect:
    """Represents a sound effect with its properties."""
    name: str
    path: Path
    volume: float = 1.0
    loop: bool = False
    fade_ms: int = 0

class SoundManager:
    """Manages sound effects and audio playback."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SoundManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._sounds: Dict[str, SoundEffect] = {}
            self._enabled: bool = True
            self._global_volume: float = 1.0
            self._muted: bool = False
            self._initialized = True
            self._initialized_pygame: bool = False
            self._initialize_audio()
    
    def _initialize_audio(self) -> None:
        """Initialize the audio system."""
        if not PYGAME_AVAILABLE:
            logger.warning("pygame not available. Sound effects will be disabled.")
            self._enabled = False
            return
        
        try:
            # Initialize pygame mixer with optimized settings
            pygame.mixer.pre_init(
                frequency=44100,  # Standard CD quality
                size=-16,        # 16-bit signed
                channels=2,      # Stereo
                buffer=512,      # Lower buffer size for less latency
                allowedchanges=(
                    pygame.AUDIO_ALLOW_FREQUENCY_CHANGE |
                    pygame.AUDIO_ALLOW_CHANNELS_CHANGE
                )
            )
            pygame.mixer.init()
            self._initialized_pygame = True
            logger.info("Audio system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize audio system: {e}")
            self._enabled = False
    
    def load_sound(self, name: str, path: Union[str, Path], 
                  volume: float = 1.0, loop: bool = False) -> bool:
        """Load a sound effect.
        
        Args:
            name: Name to identify the sound
            path: Path to the sound file
            volume: Volume level (0.0 to 1.0)
            loop: Whether to loop the sound
            
        Returns:
            bool: True if the sound was loaded successfully
        """
        if not self._enabled or not self._initialized_pygame:
            return False
        
        try:
            sound_path = Path(path)
            if not sound_path.exists():
                logger.error(f"Sound file not found: {sound_path}")
                return False
            
            # Create sound effect
            sound_effect = SoundEffect(
                name=name,
                path=sound_path,
                volume=min(max(0.0, volume), 1.0),  # Clamp to 0.0-1.0
                loop=loop
            )
            
            # Store the sound effect
            self._sounds[name.lower()] = sound_effect
            logger.debug(f"Loaded sound: {name} from {sound_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load sound {name}: {e}")
            return False
    
    def play_sound(self, name: str, volume: Optional[float] = None, 
                  loop: Optional[bool] = None, fade_ms: int = 0) -> bool:
        """Play a sound effect.
        
        Args:
            name: Name of the sound to play
            volume: Optional volume override (0.0 to 1.0)
            loop: Optional loop override
            fade_ms: Fade in time in milliseconds
            
        Returns:
            bool: True if the sound was played successfully
        """
        if not self._enabled or self._muted or not self._initialized_pygame:
            return False
        
        name = name.lower()
        if name not in self._sounds:
            logger.warning(f"Sound not found: {name}")
            return False
        
        try:
            sound_effect = self._sounds[name]
            
            # Apply overrides
            play_volume = volume if volume is not None else sound_effect.volume
            play_loop = loop if loop is not None else sound_effect.loop
            
            # Clamp volume
            play_volume = min(max(0.0, play_volume), 1.0)
            
            # Apply global volume
            play_volume *= self._global_volume
            
            # Play the sound using the system's default player as a fallback
            if not self._initialized_pygame:
                return self._play_with_system_player(sound_effect.path)
            
            # Try to play with pygame
            try:
                # Load the sound
                sound = pygame.mixer.Sound(sound_effect.path)
                
                # Set volume
                sound.set_volume(play_volume)
                
                # Play with or without fade in
                if fade_ms > 0:
                    sound.play(loops=-1 if play_loop else 0, fade_ms=fade_ms)
                else:
                    sound.play(loops=-1 if play_loop else 0)
                
                logger.debug(f"Playing sound: {name} (volume: {play_volume:.1f}, loop: {play_loop})")
                return True
                
            except Exception as e:
                logger.error(f"Failed to play sound with pygame: {e}")
                # Fall back to system player
                return self._play_with_system_player(sound_effect.path)
                
        except Exception as e:
            logger.error(f"Error playing sound {name}: {e}")
            return False
    
    def _play_with_system_player(self, sound_path: Path) -> bool:
        """Play a sound using the system's default player as a fallback."""
        try:
            system = platform.system().lower()
            
            if system == 'darwin':  # macOS
                cmd = ['afplay', str(sound_path)]
            elif system == 'windows':
                import winsound
                winsound.PlaySound(str(sound_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
                return True
            else:  # Linux and others
                # Try various Linux audio players
                for player in ['aplay', 'paplay', 'mpg123', 'mpg321', 'mplayer']:
                    if self._is_command_available(player):
                        cmd = [player, str(sound_path)]
                        break
                else:
                    logger.error("No supported audio player found")
                    return False
            
            # Start the player in a subprocess
            subprocess.Popen(cmd, 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            return True
            
        except Exception as e:
            logger.error(f"Failed to play sound with system player: {e}")
            return False
    
    def _is_command_available(self, command: str) -> bool:
        """Check if a command is available on the system."""
        try:
            return subprocess.call(['which', command], 
                                 stdout=subprocess.DEVNULL, 
                                 stderr=subprocess.DEVNULL) == 0
        except Exception:
            return False
    
    def stop_sound(self, name: str, fade_ms: int = 0) -> None:
        """Stop a playing sound.
        
        Args:
            name: Name of the sound to stop
            fade_ms: Fade out time in milliseconds
        """
        if not self._enabled or not self._initialized_pygame:
            return
        
        name = name.lower()
        if name not in self._sounds:
            return
        
        try:
            # Stop all sounds with the given name
            if fade_ms > 0:
                # Fade out all channels playing this sound
                for channel in pygame.mixer.find_channel():
                    if channel.get_sound() == self._sounds[name]:
                        channel.fadeout(fade_ms)
            else:
                # Stop immediately
                for channel in pygame.mixer.find_channel():
                    if channel.get_sound() == self._sounds[name]:
                        channel.stop()
            
        except Exception as e:
            logger.error(f"Error stopping sound {name}: {e}")
    
    def stop_all_sounds(self, fade_ms: int = 0) -> None:
        """Stop all playing sounds.
        
        Args:
            fade_ms: Fade out time in milliseconds
        """
        if not self._enabled or not self._initialized_pygame:
            return
        
        try:
            if fade_ms > 0:
                pygame.mixer.fadeout(fade_ms)
            else:
                pygame.mixer.stop()
        except Exception as e:
            logger.error(f"Error stopping all sounds: {e}")
    
    def set_volume(self, volume: float) -> None:
        """Set the global volume.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self._global_volume = min(max(0.0, volume), 1.0)  # Clamp to 0.0-1.0
        
        if self._enabled and self._initialized_pygame:
            try:
                pygame.mixer.music.set_volume(self._global_volume)
            except Exception as e:
                logger.error(f"Error setting volume: {e}")
    
    def get_volume(self) -> float:
        """Get the current global volume.
        
        Returns:
            float: Current volume level (0.0 to 1.0)
        """
        return self._global_volume
    
    def mute(self, mute: Optional[bool] = None) -> bool:
        """Toggle or set mute state.
        
        Args:
            mute: Optional mute state to set. If None, toggles the current state.
            
        Returns:
            bool: New mute state
        """
        if mute is None:
            self._muted = not self._muted
        else:
            self._muted = bool(mute)
        
        # Stop all sounds when muting
        if self._muted and self._enabled and self._initialized_pygame:
            self.stop_all_sounds()
        
        return self._muted
    
    def is_muted(self) -> bool:
        """Check if the sound is muted.
        
        Returns:
            bool: True if muted, False otherwise
        """
        return self._muted
    
    def is_enabled(self) -> bool:
        """Check if sound is enabled.
        
        Returns:
            bool: True if sound is enabled, False otherwise
        """
        return self._enabled
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self._initialized_pygame:
            try:
                self.stop_all_sounds()
                pygame.mixer.quit()
                self._initialized_pygame = False
            except Exception as e:
                logger.error(f"Error during audio cleanup: {e}")

# Global sound manager instance
sound_manager = SoundManager()

def get_sound_manager() -> SoundManager:
    """Get the global sound manager instance."""
    return sound_manager
