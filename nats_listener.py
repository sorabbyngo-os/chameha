"""
nats_listener.py — NATS mesh listener
Public:   sorabbyngo.chameha.public.*
Personal: sorabbyngo.chameha.personal.{user_id}.*
RULE: personal events NEVER touch the public bus.
"""
from __future__ import annotations
import asyncio, json, logging, os
from typing import Callable, Awaitable
import nats
from nats.aio.client import Client as NATSClient
from identity import get_node_id, get_active_user_id, get_twin_session

log = logging.getLogger("chameha.nats_listener")

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
NODE_ID  = get_node_id()

TOPIC_PUBLIC_OS       = "sorabbyngo.chameha.public.os"
TOPIC_PUBLIC_HEALTH   = "sorabbyngo.chameha.public.health"
TOPIC_PUBLIC_SECURITY = "sorabbyngo.chameha.public.security"
TOPIC_PUBLIC_ANNOUNCE = "sorabbyngo.chameha.public.announce"

def topic_personal(user_id: str, subtopic: str = "*") -> str:
    return f"sorabbyngo.chameha.personal.{user_id}.{subtopic}"

Handler = Callable[[dict], Awaitable[None]]


class NATSListener:
    def __init__(self):
        self._nc: NATSClient | None = None
        self._public_handlers:   list[tuple[str, Handler]] = []
        self._personal_handlers: list[tuple[str, Handler]] = []
        self._subs: list = []

    def on_public(self, topic: str, handler: Handler) -> None:
        self._public_handlers.append((topic, handler))

    def on_personal(self, subtopic: str, handler: Handler) -> None:
        self._personal_handlers.append((subtopic, handler))

    async def start(self) -> None:
        self._nc = await nats.connect(
            NATS_URL, name=f"chameha-{NODE_ID}",
            error_cb=self._error_cb,
            disconnected_cb=self._disconnected_cb,
            reconnected_cb=self._reconnected_cb,
        )
        log.info("NATS connected: %s (node %s)", NATS_URL, NODE_ID)
        await self._subscribe_public()
        await self._subscribe_personal()

    async def resubscribe_personal(self) -> None:
        for sub in list(self._subs):
            if hasattr(sub, "_subject") and "personal" in sub._subject:
                await sub.drain()
                self._subs.remove(sub)
        await self._subscribe_personal()

    async def stop(self) -> None:
        if self._nc:
            await self._nc.drain()

    async def publish_public(self, topic: str, payload: dict) -> None:
        if not self._nc: return
        await self._nc.publish(topic, json.dumps({**payload, "node_id": NODE_ID}).encode())

    async def publish_personal(self, user_id: str, subtopic: str, payload: dict) -> None:
        if not self._nc: return
        topic = topic_personal(user_id, subtopic)
        await self._nc.publish(topic, json.dumps({**payload, "user_id": user_id}).encode())
        log.debug("personal publish -> %s", topic)

    async def _subscribe_public(self) -> None:
        for topic, handler in self._public_handlers:
            sub = await self._nc.subscribe(topic, cb=self._make_cb(handler, "public"))
            self._subs.append(sub)
            log.info("public sub -> %s", topic)

    async def _subscribe_personal(self) -> None:
        user_id = get_active_user_id()
        if not user_id: return
        if not get_twin_session(user_id): return
        for subtopic, handler in self._personal_handlers:
            topic = topic_personal(user_id, subtopic)
            sub   = await self._nc.subscribe(topic, cb=self._make_cb(handler, "personal"))
            self._subs.append(sub)
            log.info("personal sub -> %s (user %s)", topic, user_id)

    @staticmethod
    def _make_cb(handler: Handler, mode: str):
        async def _cb(msg):
            try:
                payload = json.loads(msg.data.decode())
                await handler(payload)
            except json.JSONDecodeError:
                log.warning("malformed NATS message on %s", msg.subject)
            except Exception as e:
                log.error("handler error on %s: %s", msg.subject, e)
        return _cb

    async def _error_cb(self, e):        log.error("NATS error: %s", e)
    async def _disconnected_cb(self):    log.warning("NATS disconnected")
    async def _reconnected_cb(self):
        log.info("NATS reconnected — re-subscribing")
        await self._subscribe_public()
        await self._subscribe_personal()


async def handle_twin_updated(payload: dict) -> None:
    user_id = payload.get("user_id")
    if user_id:
        from twin_client import invalidate_cache
        invalidate_cache(user_id)
        log.info("twin context cache invalidated for %s", user_id)

async def handle_safety_flag(payload: dict) -> None:
    log.warning("SAFETY FLAG — user=%s domain=%s confidence=%.2f response_id=%s",
        payload.get("user_id"), payload.get("domain"),
        payload.get("confidence", 0), payload.get("response_id"))

async def handle_session_expire(payload: dict) -> None:
    log.info("session expire warning for %s", payload.get("user_id"))
