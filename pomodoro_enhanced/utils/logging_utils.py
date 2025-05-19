"""Utility to configure a project-wide logger and redirect print statements."""

from __future__ import annotations

import logging
import sys
from types import ModuleType


_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str | ModuleType | None = None) -> logging.Logger:
    """Return a configured project-level logger.

    The first call initialises global logging only once so subsequent calls are
    cheap.  All modules should prefer this helper over *logging.getLogger*
    directly so configuration stays consistent.
    """
    logging.basicConfig(  # No-op if called a second time
        level=logging.INFO,
        format=_LOG_FORMAT,
        datefmt=_DATE_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=False,  # Keep any basicConfig done by host environment
    )

    if isinstance(name, ModuleType):  # pragma: no cover – convenience only
        name = name.__name__
    return logging.getLogger(name)


def redirect_print_to_logger(logger: logging.Logger, level: int = logging.DEBUG) -> None:
    """Monkey-patch :pyfunc:`print` so it forwards to *logger*.

    This offers an incremental migration path from scattered *print* calls to a
    proper logging strategy.  All existing *print* invocations will now be
    captured at *level* (default: ``DEBUG``).
    """
    import builtins  # Local import to avoid polluting global namespace
    _original_print = builtins.print # Store original print for fallback

    def _log_print(*args: object, sep: str | None = " ", end: str | None = "\n", file=None, flush: bool = False):  # noqa: D401, DAR101, DAR201
        # If 'file' is specified and it's not stdout/stderr, use original print
        if file is not None and file not in (sys.stdout, sys.stderr):
            _original_print(*args, sep=sep, end=end, file=file, flush=flush)
            return

        # Handle None for sep and end, mimicking built-in print defaults
        # Python's print treats sep=None as ' ' and end=None as '\n'.
        effective_sep = " " if sep is None else sep
        effective_end = "\n" if end is None else end

        message_parts = [str(a) for a in args]
        message = effective_sep.join(message_parts) + effective_end
        
        logger.log(level, message.rstrip("\n")) # rstrip to avoid double newlines if logger adds one
        
        if flush:
            for handler in logger.handlers:
                if hasattr(handler, 'flush'): # Check if handler supports flush
                    handler.flush()

    builtins.print = _log_print  # type: ignore[assignment]
