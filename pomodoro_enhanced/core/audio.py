from __future__ import annotations

"""Light‑weight, self‑contained sound backend.

Usage
-----
>>> sm = SoundManager("default")
>>> sm.play("work_start")

`SoundManager` is deliberately agnostic about *when* to play a sound –
it simply exposes `play(event: str)`.  The UI or TimerService decides
*which* event string to push.  This keeps audio as an injectable
side‑effect, simplifying tests (swap in DummySoundManager).
"""

from pathlib import Path
from typing import Dict, Final, Iterable
import logging

try:
    import pygame  # type: ignore
except ImportError:  # pragma: no cover – audio is optional in CI
    pygame = None  # pyright: ignore[assignment]

__all__ = [
    "SoundManager",
    "NullSoundManager",
]

LOGGER: Final = logging.getLogger(__name__)


class _Sound:
    """Wrapper so we can stub in a silent replacement during tests."""

    __slots__ = ("_impl",)

    def __init__(self, impl):
        self._impl = impl

    def play(self):  # noqa: D401 – simple verb OK here.
        if self._impl:
            self._impl.play()


class SoundManager:  # pylint: disable=too-few-public-methods
    """Runtime mixer with optional fallback if *pygame* is missing."""

    #: canonical set so callers get *early* ValueError on typos
    EVENTS: Final[frozenset[str]] = frozenset(
        {
            "work_start",
            "work_end",
            "break_start",
            "break_end",
            "long_break_start",
            "reset",
            "pause",
            "resume",
            "notification",
            "achievement",
        }
    )

    _DEFAULT_EXTS: Final[tuple[str, ...]] = (".wav", ".mp3")

    def __init__(
        self,
        pack: str = "default",
        base_dir: str | Path | None = None,
        enabled: bool = True,
    ) -> None:
        self._base_dir = Path(base_dir or Path(__file__).parent.parent.parent / "sounds")
        self._enabled = enabled and pygame is not None
        self._sounds: Dict[str, _Sound] = {}

        if self._enabled:
            self._ensure_mixer()
        else:
            LOGGER.warning("Audio disabled – pygame not available or runtime flag off.")

        self.set_pack(pack)  # populates self._sounds

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def play(self, event: str) -> None:
        """Fire‑and‑forget – returns instantly."""
        if not self._enabled:
            return
        if event not in self.EVENTS:
            raise ValueError(f"Unknown sound event: {event!r}")
        try:
            self._sounds[event].play()
        except KeyError:
            LOGGER.debug("Sound for event %s not loaded – skipping", event)

    def set_enabled(self, enabled: bool) -> None:  # noqa: D401
        self._enabled = enabled and pygame is not None

    def set_pack(self, name: str) -> None:
        """Load / reload all sounds for *name* synchronously."""
        self._sounds.clear()
        if not self._enabled:
            return

        pack_path = self._base_dir / name
        if not pack_path.is_dir():
            raise FileNotFoundError(pack_path)

        for event in self.EVENTS:
            sound = self._load_sound(pack_path, event)
            if sound:
                self._sounds[event] = sound

        LOGGER.info("Loaded %d/%d sounds from '%s'", len(self._sounds), len(self.EVENTS), name)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _ensure_mixer(self) -> None:
        """Initialise *pygame* mixer lazily and exactly once."""
        if pygame.mixer.get_init():
            return
        pygame.mixer.init()
        LOGGER.debug("pygame mixer initialised → %s", pygame.mixer.get_init())

    def _load_sound(self, folder: Path, event: str) -> _Sound | None:
        for ext in self._DEFAULT_EXTS:
            candidate = folder / f"{event}{ext}"
            if candidate.exists():
                try:
                    return _Sound(pygame.mixer.Sound(candidate.as_posix()))
                except Exception as exc:  # noqa: BLE001
                    LOGGER.warning("Could not load %s: %s", candidate.name, exc)
        LOGGER.debug("No file found for %s in %s", event, folder)
        return None


class NullSoundManager(SoundManager):
    """A silent stub – useful in tests or headless CI."""

    def __init__(self):
        self._enabled = False
        self._sounds = {}
