import os
import sys


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def app_root() -> str:
    """Writable application root (config, storage)."""
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


def bundle_root() -> str:
    """Read-only bundled resources (webui, resource, config templates)."""
    if is_frozen():
        return sys._MEIPASS
    return app_root()
