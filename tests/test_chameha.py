"""
Chameha -- Test Suite
All offline — no Ollama, NATS, or real filesystem required.
"""
import json
import os
import tempfile
import time
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import pytest
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)

# ============================================================================
# EventBus
# ============================================================================
class TestEventBus:
    def test_publish_and_receive(self):
        from event_bus import EventBus, ChamehaEvent, EventType, Severity
        bus = EventBus()
        bus.start()
        received = []
        bus.subscribe(lambda e: received.append(e))
        event = ChamehaEvent(
            source="sentinel.core", event_type=EventType.LOCK,
            severity=Severity.CRITICAL, message="Threat detected",
        )
        bus.publish(event)
        time.sleep(0.1)
        bus.stop()
        assert len(received) == 1
        assert received[0].message == "Threat detected"

    def test_priority_ordering(self):
        from event_bus import EventBus, ChamehaEvent, EventType, Severity
        bus   = EventBus()
        order = []
        bus.subscribe(lambda e: order.append(e.severity))
        bus.start()
        bus.publish(ChamehaEvent("src", EventType.NOTIFY, Severity.LOW,      "low"))
        bus.publish(ChamehaEvent("src", EventType.NOTIFY, Severity.CRITICAL, "critical"))
        bus.publish(ChamehaEvent("src", EventType.NOTIFY, Severity.HIGH,     "high"))
        time.sleep(0.2)
        bus.stop()
        assert order[0] == Severity.CRITICAL

    def test_handler_error_does_not_crash(self):
        from event_bus import EventBus, ChamehaEvent, EventType, Severity
        bus   = EventBus()
        calls = []
        bus.subscribe(lambda e: (_ for _ in ()).throw(RuntimeError("crash")))
        bus.subscribe(lambda e: calls.append(e))
        bus.start()
        bus.publish(ChamehaEvent("src", EventType.NOTIFY, Severity.LOW, "test"))
        time.sleep(0.1)
        bus.stop()
        assert len(calls) == 1

    def test_should_surface_high_and_above(self):
        from event_bus import ChamehaEvent, EventType, Severity
        low  = ChamehaEvent("src", EventType.NOTIFY, Severity.LOW,      "low")
        high = ChamehaEvent("src", EventType.NOTIFY, Severity.HIGH,     "high")
        crit = ChamehaEvent("src", EventType.LOCK,   Severity.CRITICAL, "crit")
        assert low.should_surface()  is False
        assert high.should_surface() is True
        assert crit.should_surface() is True

    def test_event_to_dict(self):
        from event_bus import ChamehaEvent, EventType, Severity
        e = ChamehaEvent(
            source="byngox.health", event_type=EventType.NOTIFY,
            severity=Severity.HIGH, message="Risk elevated",
            action_taken="alert sent", confidence=0.92,
        )
        d = e.to_dict()
        assert d["source"]       == "byngox.health"
        assert d["confidence"]   == 0.92
        assert d["action_taken"] == "alert sent"

    def test_convenience_functions(self):
        from event_bus import EventBus, EventType, Severity, notify, ask, lock
        bus      = EventBus()
        received = []
        bus.subscribe(lambda e: received.append(e))
        bus.start()
        notify(bus, "test.src", "info message")
        ask(bus, "test.src", "confirm action")
        lock(bus, "test.src", "system locked", action_taken="blocked")
        time.sleep(0.2)
        bus.stop()
        types = {e.event_type for e in received}
        assert EventType.NOTIFY in types
        assert EventType.ASK    in types
        assert EventType.LOCK   in types

    def test_stop_cleanly(self):
        from event_bus import EventBus
        bus = EventBus()
        bus.start()
        bus.stop()
        assert bus._running is False

# ============================================================================
# Brain
# ============================================================================
class TestBrain:
    @pytest.fixture
    def brain_setup(self, tmp_dir):
        from event_bus import EventBus
        from brain import Brain
        bus      = EventBus()
        identity = MagicMock()
        identity.node_id = "test-node-123"
        config   = MagicMock()
        with patch("brain.AUDIT_DIR", str(tmp_dir / "audit")):
            b = Brain(bus, identity, config)
        return b, bus, tmp_dir

    def test_lock_event_surfaces(self, brain_setup):
        from event_bus import ChamehaEvent, EventType, Severity
        brain, bus, tmp_dir = brain_setup
        surfaced = []
        brain.on_surface(lambda msg, e: surfaced.append(msg))
        event = ChamehaEvent(
            source="sentinel.core", event_type=EventType.LOCK,
            severity=Severity.CRITICAL, message="Threat blocked",
            action_taken="IP blocked",
        )
        with patch("brain.AUDIT_DIR", str(tmp_dir / "audit")):
            brain._handle(event)
        assert len(surfaced) == 1
        assert "Threat blocked" in surfaced[0]

    def test_notify_low_not_surfaced(self, brain_setup):
        from event_bus import ChamehaEvent, EventType, Severity
        brain, _, tmp_dir = brain_setup
        surfaced = []
        brain.on_surface(lambda msg, e: surfaced.append(msg))
        event = ChamehaEvent(
            source="hal.sensors", event_type=EventType.NOTIFY,
            severity=Severity.LOW, message="Sensor ping",
        )
        with patch("brain.AUDIT_DIR", str(tmp_dir / "audit")):
            brain._handle(event)
        assert len(surfaced) == 0

    def test_notify_critical_surfaces(self, brain_setup):
        from event_bus import ChamehaEvent, EventType, Severity
        brain, _, tmp_dir = brain_setup
        surfaced = []
        brain.on_surface(lambda msg, e: surfaced.append(msg))
        event = ChamehaEvent(
            source="novela.risk", event_type=EventType.NOTIFY,
            severity=Severity.CRITICAL, message="Patient critical",
        )
        with patch("brain.AUDIT_DIR", str(tmp_dir / "audit")):
            brain._handle(event)
        assert len(surfaced) == 1

    def test_deduplication(self, brain_setup):
        from event_bus import ChamehaEvent, EventType, Severity
        brain, _, tmp_dir = brain_setup
        surfaced = []
        brain.on_surface(lambda msg, e: surfaced.append(msg))
        with patch("brain.AUDIT_DIR", str(tmp_dir / "audit")):
            brain._handle(ChamehaEvent(
                source="sentinel.core", event_type=EventType.LOCK,
                severity=Severity.CRITICAL, message="Same event repeated",
            ))
            brain._handle(ChamehaEvent(
                source="sentinel.core", event_type=EventType.LOCK,
                severity=Severity.CRITICAL, message="Same event repeated",
            ))
        assert len(surfaced) == 1

    def test_ask_routes_to_callback(self, brain_setup):
        from event_bus import ChamehaEvent, EventType, Severity
        brain, _, tmp_dir = brain_setup
        asked = []
        brain.on_ask(lambda e: asked.append(e))
        event = ChamehaEvent(
            source="byngox.health", event_type=EventType.ASK,
            severity=Severity.HIGH, message="Confirm treatment?",
        )
        with patch("brain.AUDIT_DIR", str(tmp_dir / "audit")):
            brain._handle(event)
        assert len(asked) == 1

    def test_source_label_mapping(self, brain_setup):
        brain, _, _ = brain_setup
        assert brain._source_label("sentinel.core")  == "Sentinel"
        assert brain._source_label("byngox.health")  == "Health Monitor"
        assert brain._source_label("novela.risk")    == "Health Risk"
        assert brain._source_label("unknown.source") == "Unknown"

    def test_audit_creates_file(self, brain_setup):
        from event_bus import ChamehaEvent, EventType, Severity
        brain, _, tmp_dir = brain_setup
        event = ChamehaEvent(
            source="test", event_type=EventType.NOTIFY,
            severity=Severity.LOW, message="audit test",
        )
        audit_dir  = tmp_dir / "audit"
        audit_file = audit_dir / "events.jsonl"
        with patch("brain.AUDIT_DIR", str(audit_dir)):
            with patch("brain.AUDIT_FILE", str(audit_file)):
                brain._audit(event)
        assert audit_file.exists()
        line = json.loads(audit_file.read_text().strip())
        assert line["message"] == "audit test"

# ============================================================================
# DeviceIdentity
# ============================================================================
class TestDeviceIdentity:
    def test_sealed_when_nodeid_found(self, tmp_dir):
        nid_file = tmp_dir / "nodeid"
        nid_file.write_text("abc123\n")
        with patch.dict(os.environ, {"NODE_ID_PATH": str(nid_file),
                                      "NODE_ID_FALLBACK_PATH": str(tmp_dir / "fallback")}):
            import identity as _id
            _id._node_id_cache = None
            from identity import DeviceIdentity
            d = DeviceIdentity()
        assert d.sealed  is True
        assert d.node_id == "abc123"

    def test_not_sealed_when_missing(self, tmp_dir):
        with patch.dict(os.environ, {"NODE_ID_PATH": str(tmp_dir / "nonexistent"),
                                      "NODE_ID_FALLBACK_PATH": str(tmp_dir / "fallback")}):
            import identity as _id
            _id._node_id_cache = None
            from identity import DeviceIdentity
            d = DeviceIdentity()
        assert d.sealed  is False
        assert d.node_id is not None   # derived fallback

    def test_short_id(self, tmp_dir):
        nid_file = tmp_dir / "nodeid"
        nid_file.write_text("abcdef123456789xyz")
        with patch.dict(os.environ, {"NODE_ID_PATH": str(nid_file),
                                      "NODE_ID_FALLBACK_PATH": str(tmp_dir / "fallback")}):
            import identity as _id
            _id._node_id_cache = None
            from identity import DeviceIdentity
            d = DeviceIdentity()
        assert len(d.short_id()) == 12
        assert d.short_id() == "abcdef123456"

    def test_assert_sealed_raises_when_not_sealed(self, tmp_dir):
        with patch.dict(os.environ, {"NODE_ID_PATH": str(tmp_dir / "nonexistent"),
                                      "NODE_ID_FALLBACK_PATH": str(tmp_dir / "fallback")}):
            import identity as _id
            _id._node_id_cache = None
            from identity import DeviceIdentity
            d = DeviceIdentity()
        d.sealed = False
        with pytest.raises(RuntimeError, match="NodeID not found"):
            d.assert_sealed()

    def test_assert_sealed_passes_when_sealed(self, tmp_dir):
        nid_file = tmp_dir / "nodeid"
        nid_file.write_text("nodeid123")
        with patch.dict(os.environ, {"NODE_ID_PATH": str(nid_file),
                                      "NODE_ID_FALLBACK_PATH": str(tmp_dir / "fallback")}):
            import identity as _id
            _id._node_id_cache = None
            from identity import DeviceIdentity
            d = DeviceIdentity()
        d.assert_sealed()  # should not raise

    def test_not_sealed_when_permission_error(self, tmp_dir):
        with patch.dict(os.environ, {"NODE_ID_PATH": "/proc/sorabbyngo/nodeid",
                                      "NODE_ID_FALLBACK_PATH": str(tmp_dir / "fallback")}):
            with patch("identity.open", side_effect=PermissionError):
                import identity as _id
                _id._node_id_cache = None
                from identity import DeviceIdentity
                d = DeviceIdentity()
        assert d.sealed is False

# ============================================================================
# UserConfig
# ============================================================================
class TestUserConfig:
    @pytest.fixture
    def config(self, tmp_dir):
        from identity import DeviceIdentity
        from config import UserConfig
        nid_file = tmp_dir / "nodeid"
        nid_file.write_text("test-node-id")
        with patch.dict(os.environ, {
            "NODE_ID_PATH": str(nid_file),
            "NODE_ID_FALLBACK_PATH": str(tmp_dir / "fallback"),
            "CHAMEHA_CONFIG_DIR": str(tmp_dir),
        }):
            import identity as _id
            _id._node_id_cache = None
            identity = DeviceIdentity()
            c = UserConfig(identity)
        return c, identity, tmp_dir

    def test_default_first_boot(self, config):
        c, _, _ = config
        assert c.is_first_boot() is True
        assert c.name  == "friend"
        assert c.boots == 0

    def test_complete_first_boot(self, config):
        c, _, tmp_dir = config
        with patch.dict(os.environ, {"CHAMEHA_CONFIG_DIR": str(tmp_dir)}):
            c.complete_first_boot("Jonah")
        assert c.name           == "Jonah"
        assert c.is_first_boot() is False
        assert c.boots           == 1

    def test_increment_boot(self, config):
        c, _, tmp_dir = config
        with patch.dict(os.environ, {"CHAMEHA_CONFIG_DIR": str(tmp_dir)}):
            c.increment_boot()
            c.increment_boot()
        assert c.boots == 2

    def test_region_default(self, config):
        c, _, _ = config
        assert c.region == "KE"

    def test_node_id_mismatch_resets(self, tmp_dir):
        import json as _json
        from identity import DeviceIdentity
        from config import UserConfig
        cfg_file = tmp_dir / "user.json"
        cfg_file.write_text(_json.dumps({
            "node_id": "different-node", "name": "Alice",
            "boots": 10, "first_boot_complete": True,
            "locale": "sw", "region": "KE",
        }))
        nid_file = tmp_dir / "nodeid"
        nid_file.write_text("my-actual-node")
        with patch.dict(os.environ, {
            "NODE_ID_PATH": str(nid_file),
            "NODE_ID_FALLBACK_PATH": str(tmp_dir / "fallback"),
            "CHAMEHA_CONFIG_DIR": str(tmp_dir),
        }):
            import identity as _id
            _id._node_id_cache = None
            identity = DeviceIdentity()
            c = UserConfig(identity)
        assert c.is_first_boot() is True

# ============================================================================
# Tier 1
# ============================================================================
class TestTier1:
    def test_detect_english(self):
        from tier1 import _detect_language
        assert _detect_language("What is the weather today?") == "en"

    def test_detect_swahili(self):
        from tier1 import _detect_language
        assert _detect_language("Habari yako, dawa ya mgonjwa") == "sw"

    def test_detect_hausa(self):
        from tier1 import _detect_language
        assert _detect_language("Yauwa lafiya magani") == "ha"

    def test_ollama_unreachable_not_available(self):
        from tier1 import Tier1
        with patch("urllib.request.urlopen", side_effect=Exception("timeout")):
            t = Tier1()
        assert t.available is False

    def test_chat_fallback_when_offline(self):
        from tier1 import Tier1
        with patch("urllib.request.urlopen", side_effect=Exception("offline")):
            t = Tier1()
        response = t.chat("Hello")
        assert "warming up" in response.lower() or "Sorabbyngo" in response

    def test_device_command_offline(self):
        from tier1 import Tier1
        with patch("urllib.request.urlopen", side_effect=Exception("offline")):
            t = Tier1()
        result = t.device_command("turn on wifi")
        assert result["error"] is not None

    def test_status_offline(self):
        from tier1 import Tier1
        with patch("urllib.request.urlopen", side_effect=Exception("offline")):
            t = Tier1()
        assert "offline" in t.status().lower()

    def test_get_tier1_singleton(self):
        import tier1
        tier1._tier1 = None
        with patch("urllib.request.urlopen", side_effect=Exception("offline")):
            a = tier1.get_tier1()
            b = tier1.get_tier1()
        assert a is b

# ============================================================================
# Tier 2
# ============================================================================
class TestTier2:
    def test_not_available_without_gpu(self):
        from tier2 import Tier2
        with patch("tier2._check_gpu", return_value=False):
            t = Tier2()
        assert t.available is False

    def test_status_offline(self):
        from tier2 import Tier2
        with patch("tier2._check_gpu", return_value=False):
            t = Tier2()
        assert "offline" in t.status().lower()

    def test_chat_raises_when_unavailable(self):
        from tier2 import Tier2
        with patch("tier2._check_gpu", return_value=False):
            t = Tier2()
        with pytest.raises(RuntimeError, match="Tier 2 unavailable"):
            t.chat("test")

    def test_reason_raises_when_unavailable(self):
        from tier2 import Tier2
        with patch("tier2._check_gpu", return_value=False):
            t = Tier2()
        with pytest.raises(RuntimeError):
            t.reason("complex query")

    def test_get_tier2_singleton(self):
        import tier2
        tier2._tier2 = None
        with patch("tier2._check_gpu", return_value=False):
            a = tier2.get_tier2()
            b = tier2.get_tier2()
        assert a is b

# ============================================================================
# Tier 3
# ============================================================================
class TestTier3:
    @pytest.fixture
    def tier3(self):
        from tier3 import Tier3
        with patch("tier3.Tier3._check_available", return_value=False):
            return Tier3()

    def test_sanitize_ip_address(self, tier3):
        result = tier3._sanitize("Connect to 192.168.1.100 for data")
        assert "192.168.1.100" not in result
        assert "[REDACTED_IP]" in result

    def test_sanitize_proc_path(self, tier3):
        result = tier3._sanitize("Read /proc/sorabbyngo/nodeid now")
        assert "/proc/sorabbyngo/nodeid" not in result
        assert "[REDACTED_PATH]" in result

    def test_sanitize_home_path(self, tier3):
        result = tier3._sanitize("File at /home/jonah/secret.txt")
        assert "/home/jonah" not in result

    def test_sanitize_hash(self, tier3):
        # 64-char hex hash (sha256)
        sha256 = "a" * 64
        result = tier3._sanitize(f"Hash: {sha256}")
        assert sha256 not in result
        assert "[REDACTED_HASH]" in result

    def test_unavailable_returns_message(self, tier3):
        result = tier3.respond("test query")
        assert "unavailable" in result.lower()

    def test_check_available_unreachable(self):
        from tier3 import Tier3
        with patch("socket.socket") as mock_sock:
            mock_sock.return_value.connect.side_effect = ConnectionRefusedError
            t = Tier3()
        assert t.available is False

# ============================================================================
# Conversation routing
# ============================================================================
class TestConversation:
    @pytest.fixture
    def router(self):
        from conversation import ConversationRouter
        with patch("tier1.Tier1._check_ollama", return_value=False), \
             patch("tier2._check_gpu", return_value=False), \
             patch("tier3.Tier3._check_available", return_value=False):
            return ConversationRouter()

    def test_cloud_routes_tier3(self, router):
        router.t3.infer = MagicMock(return_value="Tier 3 response")
        result = router.handle("/cloud What is malaria?", {})
        assert result == "Tier 3 response"

    def test_tier1_used_for_simple_query(self, router):
        router.t1.infer = MagicMock(return_value="Simple response")
        result = router.handle("Hello", {})
        assert result == "Simple response"

    def test_tier2_used_for_complex_query(self, router):
        router.t2.infer = MagicMock(return_value="Complex response")
        result = router.handle("explain step by step how to manage diabetes treatment", {})
        assert result == "Complex response"

    def test_personal_mode_when_session_active(self, router):
        from twin_client import TwinUnavailable
        with patch("conversation.get_active_user_id", return_value="user-123"), \
             patch("conversation.get_twin_session", return_value=MagicMock(user_id="user-123")), \
             patch("conversation.fetch_twin_context", return_value=TwinUnavailable("user-123", "test")):
            router.t1.infer = MagicMock(return_value="Personal response")
            result = router.handle("Hello", {})
            assert result is not None

    def test_is_complex_long_query(self):
        from conversation import _is_complex
        # New threshold is 80 words not 130 chars
        long_query = " ".join(["word"] * 90)
        assert _is_complex(long_query) is True

    def test_is_complex_cue_word(self):
        from conversation import _is_complex
        assert _is_complex("explain how the heart works") is True

    def test_is_not_complex_short_casual(self):
        from conversation import _is_complex
        assert _is_complex("Hello") is False

    def test_detect_domain_medical(self):
        from conversation import _detect_domain
        assert _detect_domain("I have diabetes and need medication treatment") == "medical"

    def test_detect_domain_financial(self):
        from conversation import _detect_domain
        assert _detect_domain("What is a good investment portfolio?") == "financial"

    def test_detect_domain_general(self):
        from conversation import _detect_domain
        assert _detect_domain("What is the weather today?") == "general"

# ============================================================================
# NATS Listener
# ============================================================================
class TestNatsListener:
    def test_nats_listener_instantiates(self):
        from nats_listener import NATSListener
        listener = NATSListener()
        assert listener is not None

    def test_nats_listener_alias(self):
        from nats_listener import NatsListener, NATSListener
        assert NatsListener is NATSListener

    def test_on_public_registers_handler(self):
        from nats_listener import NATSListener
        listener = NATSListener()
        handler  = MagicMock()
        listener.on_public("test.topic", handler)
        topics = [t for t, _ in listener._public_handlers]
        assert "test.topic" in topics

    def test_on_personal_registers_handler(self):
        from nats_listener import NATSListener
        listener = NATSListener()
        handler  = MagicMock()
        listener.on_personal("twin.*", handler)
        topics = [t for t, _ in listener._personal_handlers]
        assert "twin.*" in topics

    def test_topic_personal_format(self):
        from nats_listener import topic_personal
        result = topic_personal("user-123", "health")
        assert "user-123" in result
        assert "health" in result

    def test_twin_updated_handler(self):
        import asyncio
        from nats_listener import handle_twin_updated
        with patch("twin_client.invalidate_cache") as mock_inv:
            asyncio.run(handle_twin_updated({"user_id": "user-abc"}))
            mock_inv.assert_called_once_with("user-abc")

    def test_session_expire_handler(self):
        import asyncio
        from nats_listener import handle_session_expire
        # handle_session_expire logs the expiry — just verify it runs without error
        asyncio.run(handle_session_expire({"user_id": "user-xyz"}))

# ============================================================================
# Tone Engine
# ============================================================================
class TestToneEngine:
    def test_default_mode_patient(self):
        from personality.tone_engine import ToneEngine
        t = ToneEngine()
        assert t.current_mode == "patient"

    def test_set_mode_doctor(self):
        from personality.tone_engine import ToneEngine
        t = ToneEngine()
        t.set_mode("doctor")
        assert t.current_mode == "doctor"
        assert "clinical" in t.get_style()

    def test_set_mode_developer(self):
        from personality.tone_engine import ToneEngine
        t = ToneEngine()
        t.set_mode("developer")
        assert "technical" in t.get_style()

    def test_get_greeting_with_name(self):
        from personality.tone_engine import ToneEngine
        t = ToneEngine()
        assert "Jonah" in t.get_greeting("Jonah")
        assert "Sorabbyngo" in t.get_greeting("Jonah")

    def test_get_greeting_without_name(self):
        from personality.tone_engine import ToneEngine
        t = ToneEngine()
        assert len(t.get_greeting()) > 0

    def test_invalid_mode_ignored(self):
        from personality.tone_engine import ToneEngine
        t = ToneEngine()
        t.set_mode("nonexistent")
        assert t.current_mode == "patient"

# ============================================================================
# Language Detection
# ============================================================================
class TestLanguageDetect:
    def test_english_default(self):
        from personality.language_detect import detect_language
        assert detect_language("Hello how are you?") == "en"

    def test_swahili_detected(self):
        from personality.language_detect import detect_language
        assert detect_language("Habari yako? Asante sana daktari") == "sw"

    def test_mixed_detected_as_swahili_when_2_markers(self):
        from personality.language_detect import detect_language
        assert detect_language("habari dawa") == "sw"

    def test_one_marker_not_enough(self):
        from personality.language_detect import detect_language
        assert detect_language("habari how are you today?") == "en"

    def test_response_hint_english(self):
        from personality.language_detect import get_response_language_hint
        assert "English" in get_response_language_hint("Good morning")

    def test_response_hint_swahili(self):
        from personality.language_detect import get_response_language_hint
        assert "Swahili" in get_response_language_hint("Habari yako daktari asante")
