"""
identity.py — Chameha OS identity layer
Reads NodeID from kernel driver at /proc/sorabbyngo/nodeid
Falls back to /etc/sorabbyngo/node_id or derives from hardware.
Seals every Chameha session to this specific device.
"""
import hashlib
import logging
import os
import uuid
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

# Kernel driver path (sorabbyngo_nodeid.ko)
NODE_ID_PATH = os.environ.get("NODE_ID_PATH", "/proc/sorabbyngo/nodeid")

# Fallback — generated and cached on first boot
def _get_fallback_path() -> Path:
    return Path(os.environ.get("NODE_ID_FALLBACK_PATH",
                os.path.expanduser("~/.sorabbyngo/nodeid")))

_FALLBACK_PATH = _get_fallback_path()

_node_id_cache: Optional[str] = None


def _read_node_id() -> Optional[str]:
    """Read NodeID from kernel driver."""
    path = os.environ.get("NODE_ID_PATH", NODE_ID_PATH)
    try:
        text = open(path).read().strip()
        if text:
            return text
    except (FileNotFoundError, PermissionError):
        pass
    return None


def _derive_node_id() -> str:
    """Derive a stable NodeID from hardware when kernel module unavailable."""
    global _node_id_cache
    if _node_id_cache:
        return _node_id_cache

    # Try cached fallback first
    try:
        fb = _get_fallback_path()
        if fb.exists():
            nid = fb.read_text().strip()
            if nid:
                _node_id_cache = nid
                return nid
    except Exception:
        pass

    # Derive from machine-id + MAC
    machine_id = ""
    for path in ["/etc/machine-id", "/var/lib/dbus/machine-id"]:
        try:
            machine_id = open(path).read().strip()
            break
        except Exception:
            pass

    mac = hex(uuid.getnode())
    nid = hashlib.sha256(f"{machine_id}:{mac}".encode()).hexdigest()[:24]

    # Cache to disk
    try:
        fb = _get_fallback_path()
        fb.parent.mkdir(parents=True, exist_ok=True)
        fb.write_text(nid)
    except Exception:
        pass

    log.info("NodeID derived (dev mode): %s...", nid[:12])
    _node_id_cache = nid
    return nid


class DeviceIdentity:
    def __init__(self):
        self.node_id = _read_node_id()
        self.sealed  = self.node_id is not None
        if not self.sealed:
            # Dev/QEMU mode — derive from hardware
            self.node_id = _derive_node_id()

    def short_id(self) -> str:
        """First 12 chars of NodeID for display."""
        if self.node_id:
            return self.node_id[:12]
        return "unknown"

    def assert_sealed(self):
        """Call at boot — fails loud if kernel NodeID is missing."""
        if not self.sealed:
            raise RuntimeError(
                "FATAL: NodeID not found at /proc/sorabbyngo/nodeid\n"
                "Chameha cannot run without a sealed device identity.\n"
                "Ensure the sorabbyngo kernel module is loaded."
            )

    def __repr__(self):
        return f"DeviceIdentity(node_id={self.short_id()}..., sealed={self.sealed})"


# ── Session management ────────────────────────────────────────────────────────

import time as _time

class TwinSessionInfo:
    """Active user session bound to device NodeID."""
    def __init__(self, user_id: str, twin_id: str, created_at: float = None):
        self.user_id    = user_id
        self.twin_id    = twin_id
        self.created_at = created_at or _time.time()

    def __repr__(self):
        return f"TwinSessionInfo(user={self.user_id[:8]}..., twin={self.twin_id[:8]}...)"


_active_user_id: Optional[str]        = None
_twin_sessions:  dict                  = {}


def get_node_id() -> str:
    """Get device NodeID — reads from kernel driver or derives fallback."""
    nid = _read_node_id()
    if nid:
        return nid
    return _derive_node_id()


def set_active_user(user_id: str):
    """Set the currently active user (called at login)."""
    global _active_user_id
    _active_user_id = user_id
    log.info("Active user set: %s...", user_id[:8] if user_id else "none")


def get_active_user_id() -> Optional[str]:
    """Get the currently active user ID."""
    return _active_user_id


def create_twin_session(user_id: str, twin_id: str) -> TwinSessionInfo:
    """Create a new twin session for a user."""
    session = TwinSessionInfo(user_id=user_id, twin_id=twin_id)
    _twin_sessions[user_id] = session
    log.info("Twin session created: user=%s... twin=%s...", user_id[:8], twin_id[:8])
    return session


def get_twin_session(user_id: str) -> Optional[TwinSessionInfo]:
    """Get active twin session for a user, or None."""
    return _twin_sessions.get(user_id)


def clear_session(user_id: str):
    """Clear session on logout."""
    global _active_user_id
    _twin_sessions.pop(user_id, None)
    if _active_user_id == user_id:
        _active_user_id = None
