import os
import sys


class StatusLogger:
    _COLORS = {
        "green": "\033[92m",
        "red": "\033[91m",
        "reset": "\033[0m",
    }

    def __init__(self):
        self._use_color = sys.stdout.isatty() and os.getenv("NO_COLOR", "").lower() not in ("1", "true", "yes")

    def _format(self, label: str, color: str) -> str:
        if not self._use_color:
            return label
        return f"{self._COLORS[color]}{label}{self._COLORS['reset']}"

    def success(self, message: str):
        print(f"{self._format('SUCCESS', 'green')}: {message}")

    def failure(self, message: str):
        print(f"{self._format('FAILED', 'red')}: {message}")


_LOGGER = StatusLogger()


def log_success(message: str):
    _LOGGER.success(message)


def log_failure(message: str):
    _LOGGER.failure(message)
