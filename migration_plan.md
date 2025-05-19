# Pomodoro Timer Migration Plan

This document outlines the step-by-step approach for migrating from the monolithic `pomodoro.py` to the modular `pomodoro_enhanced` package structure.

## Phase 1: Integrate Core Components (Current Focus)

### Audio Integration (✅ Started)

1. **Sound Manager** (`core/audio.py`)
   - ✅ Create `SoundManager` class with clean API
   - ✅ Create integration example (`timer_integration_example.py`)
   - ⬜ Add unit tests for SoundManager
   - ⬜ Integrate with TimerService (`timer_service.py`) 

2. **Theme Integration**
   - ✅ ThemeManager already exists (`core/theme.py`)
   - ⬜ Create integration point between legacy UI code and ThemeManager
   - ⬜ Update `update_ui_colors` method to use ThemeManager

## Phase 2: Extract Main Components

3. **TimerCore Logic Extraction**
   - ⬜ Move timer business logic from `pomodoro.py` to `timer_service.py`
   - ⬜ Create adapter layer in `pomodoro.py` to use new TimerService
   - ⬜ Add callbacks to propagate timer events to UI

4. **UI Refactoring**
   - ⬜ Determine which UI components should be extracted into widgets
   - ⬜ Create widget components for key UI elements (TimerDisplay, ControlPanel, etc.)
   - ⬜ Migrate popup windows to separate classes

## Phase 3: Wrap-Up and Mainline

5. **Main App Integration**
   - ⬜ Update `__main__.py` to use all refactored components
   - ⬜ Create launcher that can choose between monolithic and modular versions
   - ⬜ Deprecate functions in `pomodoro.py` in favor of `pomodoro_enhanced` equivalents

6. **Final Cleanup**
   - ⬜ Remove unused code from `pomodoro.py`
   - ⬜ Add documentation
   - ⬜ Run code quality tools (black, ruff, mypy)
   - ⬜ Update README and setup instructions

## Migration Strategy

1. **Create Interim Adapter Layer**:
   ```python
   # In pomodoro.py
   from pomodoro_enhanced.core.audio import SoundManager
   from pomodoro_enhanced.core.theme import ThemeManager
   
   # Then inside PomodoroTimer class
   def __init__(self, root):
       # Legacy init remains, but delegates to enhanced implementations
       self.sound_manager = SoundManager(
           pack=getattr(self.settings, 'sound_pack', 'default'),
           enabled=getattr(self.settings, 'sound_enabled', True)
       )
       self.theme_mgr = ThemeManager.get_instance()
       
       # Remaining init...
   
   def play_sound_async(self, sound_key):
       """Just delegate to sound_manager"""
       self.sound_manager.play(sound_key)
   
   def _update_theme_colors(self):
       """Delegate theme handling to ThemeManager"""
       # Get theme from manager
       theme = self.theme_mgr.get_current_theme()
       
       # Apply colors from the unified theme system
       self.bg_color = theme["colors"]["background"]
       self.fg_color = theme["colors"]["on_background"]
       self.primary_color = theme["colors"]["primary"]
       # ...etc
   ```

2. **Incremental Function Migration**:
   - One by one, replace methods in `pomodoro.py` with calls to the enhanced modules
   - Start with the most isolated functions (sound, theme) and move to more coupled ones
   - Maintain both implementations running side-by-side until migration is complete

## Next Immediate Steps:

1. Update the PomodoroTimer initialization to use the new SoundManager
2. Create a bridge that allows the existing code to utilize ThemeManager
3. Remove the sound thread and queue mechanism from pomodoro.py
4. Add unit tests for the SoundManager implementation

## Testing Approach

For each migrated component:
1. Create unit tests that verify expected behavior
2. Compare output between legacy and enhanced implementations
3. Create regression tests for key user flows
