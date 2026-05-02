"""
twin_client.py — Personal Chameha <-> Digital Twin API bridge
"""
from __future__ import annotations
import os, time, logging, threading
from dataclasses import dataclass, field
from typing import Optional
import requests

log = logging.getLogger("chameha.twin_client")

TWIN_API_BASE = os.getenv("TWIN_API_BASE", "http://localhost:8741")
TWIN_API_KEY  = os.getenv("TWIN_API_KEY", "")
TWIN_TIMEOUT  = int(os.getenv("TWIN_TIMEOUT_S", "4"))
CACHE_TTL_S   = int(os.getenv("TWIN_CACHE_TTL_S", "60"))

@dataclass
class TwinContext:
    user_id:       str
    display_name:  str
    language:      str = "en"
    personality:   dict = field(default_factory=dict)
    memory_nodes:  list[dict] = field(default_factory=list)
    domain_levels: dict = field(default_factory=dict)
    safety_flags:  list[str] = field(default_factory=list)
    fetched_at:    float = field(default_factory=time.time)

    def is_stale(self) -> bool:
        return (time.time() - self.fetched_at) > CACHE_TTL_S

    def system_prompt_block(self) -> str:
        mem_summary = "\n".join(
            f"  - [{n['category']}] {n['summary']} (confidence {n['confidence']:.0%})"
            for n in self.memory_nodes[:12]
        )
        personality_str = ", ".join(f"{k}={v}" for k, v in self.personality.items())
        return (
            f"You are {self.display_name}'s Personal Chameha — their digital twin voice.\n"
            f"Personality profile: {personality_str}\n"
            f"What you know about {self.display_name}:\n{mem_summary}\n"
            f"Respond in: {self.language}. "
            f"Warm, direct, speaks as if you know this person deeply — because you do.\n"
            f"SAFETY: domains {self.safety_flags} require a professional-advice disclaimer "
            f"and human review flag before responding."
        )

@dataclass
class TwinUnavailable:
    user_id: str
    reason:  str

_cache: dict[str, TwinContext] = {}
_cache_lock = threading.Lock()

def _get_cached(user_id: str) -> Optional[TwinContext]:
    with _cache_lock:
        ctx = _cache.get(user_id)
        if ctx and not ctx.is_stale():
            return ctx
        return None

def _set_cached(ctx: TwinContext) -> None:
    with _cache_lock:
        _cache[ctx.user_id] = ctx

def _headers() -> dict:
    h = {"Content-Type": "application/json", "X-Chameha-Node": os.getenv("NODE_ID", "unknown")}
    if TWIN_API_KEY:
        h["Authorization"] = f"Bearer {TWIN_API_KEY}"
    return h

def fetch_twin_context(user_id: str, force: bool = False) -> TwinContext | TwinUnavailable:
    if not force:
        cached = _get_cached(user_id)
        if cached:
            log.debug("twin context cache hit for %s", user_id)
            return cached
    url = f"{TWIN_API_BASE}/v1/twin/{user_id}/context"
    try:
        r = requests.get(url, headers=_headers(), timeout=TWIN_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        ctx = TwinContext(
            user_id=user_id,
            display_name=data.get("display_name", user_id),
            language=data.get("language", "en"),
            personality=data.get("personality", {}),
            memory_nodes=data.get("memory_nodes", []),
            domain_levels=data.get("domain_levels", {}),
            safety_flags=data.get("safety_flags", []),
        )
        _set_cached(ctx)
        log.info("twin context fetched for %s (%d memory nodes)", user_id, len(ctx.memory_nodes))
        return ctx
    except requests.Timeout:
        log.warning("twin API timeout for %s — falling back to public mode", user_id)
        return TwinUnavailable(user_id=user_id, reason="timeout")
    except requests.HTTPError as e:
        log.warning("twin API HTTP %s for %s", e.response.status_code, user_id)
        return TwinUnavailable(user_id=user_id, reason=f"http_{e.response.status_code}")
    except Exception as e:
        log.error("twin API error for %s: %s", user_id, e)
        return TwinUnavailable(user_id=user_id, reason="error")

def push_interaction(user_id: str, role: str, content: str, domain: str = "general") -> None:
    def _push():
        try:
            requests.post(
                f"{TWIN_API_BASE}/v1/twin/{user_id}/interactions",
                json={"role": role, "content": content, "domain": domain},
                headers=_headers(), timeout=TWIN_TIMEOUT,
            )
        except Exception as e:
            log.warning("twin push_interaction failed for %s: %s", user_id, e)
    threading.Thread(target=_push, daemon=True).start()

def invalidate_cache(user_id: str) -> None:
    with _cache_lock:
        _cache.pop(user_id, None)
    log.debug("twin context cache cleared for %s", user_id)
