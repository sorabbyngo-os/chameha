"""
identity.py — Device identity + TwinSession management
NodeID: hardware seal (unchanged)
TwinSession: per-user auth binding for Personal Chameha (new)
"""
from __future__ import annotations
import hashlib, hmac, logging, os, time, uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

log = logging.getLogger("chameha.identity")

_NODE_ID_PATH  = Path(os.getenv("NODE_ID_PATH", "/etc/sorabbyngo/node_id"))
_node_id_cache: Optional[str] = None

def get_node_id() -> str:
    global _node_id_cache
    if _node_id_cache:
        return _node_id_cache
    if _NODE_ID_PATH.exists():
        _node_id_cache = _NODE_ID_PATH.read_text().strip()
        return _node_id_cache
    machine_id = _read_machine_id()
    mac = _read_mac()
    node_id = hashlib.sha256(f"{machine_id}:{mac}".encode()).hexdigest()[:24]
    _NODE_ID_PATH.parent.mkdir(parents=True, exist_ok=True)
    _NODE_ID_PATH.write_text(node_id)
    log.info("NodeID generated: %s", node_id)
    _node_id_cache = node_id
    return node_id

def _read_machine_id() -> str:
    for path in ["/etc/machine-id", "/var/lib/dbus/machine-id"]:
        p = Path(path)
        if p.exists():
            return p.read_text().strip()
    return str(uuid.getnode())

def _read_mac() -> str:
    try:
        import netifaces
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface)
            mac = addrs.get(netifaces.AF_LINK, [{}])[0].get("addr", "")
            if mac and mac != "00:00:00:00:00:00":
                return mac
    except ImportError:
        pass
    return format(uuid.getnode(), "012x")

_SESSION_SECRET = os.getenv("TWIN_SESSION_SECRET", get_node_id())
_SESSION_TTL_S  = int(os.getenv("TWIN_SESSION_TTL_S", str(8 * 3600)))
_active_sessions: dict[str, "_TwinSession"] = {}

@dataclass
class _TwinSession:
    user_id:    str
    twin_id:    str
    token:      str
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + _SESSION_TTL_S)

    def is_valid(self) -> bool:
        return time.time() < self.expires_at

@dataclass
class TwinSessionInfo:
    user_id:    str
    twin_id:    str
    expires_at: float

    @property
    def display_ttl(self) -> str:
        remaining = max(0, int(self.expires_at - time.time()))
        h, m = divmod(remaining // 60, 60)
        return f"{h}h {m}m remaining"

def _sign_token(user_id: str, twin_id: str, created_at: float) -> str:
    message = f"{get_node_id()}:{user_id}:{twin_id}:{created_at:.0f}"
    return hmac.new(
        _SESSION_SECRET.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()

def create_twin_session(user_id: str, twin_id: str) -> TwinSessionInfo:
    created_at = time.time()
    token = _sign_token(user_id, twin_id, created_at)
    session = _TwinSession(
        user_id=user_id, twin_id=twin_id, token=token,
        created_at=created_at, expires_at=created_at + _SESSION_TTL_S,
    )
    _active_sessions[user_id] = session
    log.info("TwinSession created for user %s (twin %s)", user_id, twin_id)
    return TwinSessionInfo(user_id=user_id, twin_id=twin_id, expires_at=session.expires_at)

def get_twin_session(user_id: str) -> Optional[TwinSessionInfo]:
    session = _active_sessions.get(user_id)
    if not session:
        return None
    if not session.is_valid():
        log.info("TwinSession expired for %s — dropping to public mode", user_id)
        destroy_twin_session(user_id)
        return None
    return TwinSessionInfo(user_id=session.user_id, twin_id=session.twin_id, expires_at=session.expires_at)

def destroy_twin_session(user_id: str) -> None:
    if user_id in _active_sessions:
        del _active_sessions[user_id]
        try:
            from twin_client import invalidate_cache
            invalidate_cache(user_id)
        except ImportError:
            pass
        log.info("TwinSession destroyed for %s — returned to public mode", user_id)

def get_active_user_id() -> Optional[str]:
    for user_id, session in list(_active_sessions.items()):
        if session.is_valid():
            return user_id
        destroy_twin_session(user_id)
    return None
