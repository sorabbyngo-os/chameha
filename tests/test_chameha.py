"""
Chameha -- Test Suite
Tests: event bus, brain routing, identity, config, tier1 language detection,
       tier2 model selection, tier3 sanitization, conversation routing,
       nats listener dispatch, tone engine, language detection.
All offline -- no Ollama, NATS, or real filesystem required.
"""
import json
import os
import tempfile
import time
import queue
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
            source     = "sentinel.core",
            event_type = EventType.LOCK,
            severity   = Severity.CRITICAL,
            message    = "Threat detected",
        )
        bus.publish(event)
        time.sleep(0.1)
        bus.stop()

        assert len(received) == 1
        assert received[0].message == "Threat detected"

    def test_priority_ordering(self):
        from event_bus import EventBus, ChamehaEvent, EventType, Severity
        bus = EventBus()
        order = []

        def handler(e):
            order.append(e.severity)

        bus.subscribe(handler)
        bus.start()

        bus.publish(ChamehaEvent("src", EventType.NOTIFY, Severity.LOW,      "low"))
        bus.publish(ChamehaEvent("src", EventType.NOTIFY, Severity.CRITICAL, "critical"))
        bus.publish(ChamehaEvent("src", EventType.NOTIFY, Severity.HIGH,     "high"))
        time.sleep(0.2)
        bus.stop()

        # CRITICAL should come first (highest priority = lowest number in queue)
        assert order[0] == Severity.CRITICAL

    def test_handler_error_does_not_crash(self):
        from event_bus import EventBus, ChamehaEvent, EventType, Severity
        bus = EventBus()
        calls = []

        def bad_handler(e):
            raise RuntimeError("handler crash")

        def good_handler(e):
            calls.append(e)

        bus.subscribe(bad_handler)
        bus.subscribe(good_handler)
        bus.start()
        bus.publish(ChamehaEvent("src", EventType.NOTIFY, Severity.LOW, "test"))
        time.sleep(0.1)
        bus.stop()
        assert len(calls) == 1

    def test_should_surface_high_and_above(self):
        from event_bus import ChamehaEvent, EventType, Severity
        low  = ChamehaEvent("src", EventType.NOTIFY, Severity.LOW,    "low")
        high = ChamehaEvent("src", EventType.NOTIFY, Severity.HIGH,   "high")
        crit = ChamehaEvent("src", EventType.LOCK,   Severity.CRITICAL, "crit")
        assert low.should_surface()  is False
        assert high.should_surface() is True
        assert crit.should_surface() is True

    def test_event_to_dict(self):
        from event_bus import ChamehaEvent, EventType, Severity
        e = ChamehaEvent(
            source       = "byngox.health",
            event_type   = EventType.NOTIFY,
            severity     = Severity.HIGH,
            message      = "Risk elevated",
            action_taken = "alert sent",
            confidence   = 0.92,
        )
        d = e.to_dict()
        assert d["source"]       == "byngox.health"
        assert d["message"]      == "Risk elevated"
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

        return b, bus

    def test_lock_event_surfaces(self, brain_setup, tmp_dir):
        from event_bus import ChamehaEvent, EventType, Severity
        brain, bus = brain_setup
        surfaced = []
        brain.on_surface(lambda msg, e: surfaced.append(msg))

        event = ChamehaEvent(
            source     = "sentinel.core",
            event_type = EventType.LOCK,
            severity   = Severity.CRITICAL,
            message    = "Threat blocked",
            action_taken = "IP blocked",
        )
        with patch("brain.AUDIT_DIR", str(tmp_dir / "audit")):
            brain._handle(event)

        assert len(surfaced) == 1
        assert "Threat blocked" in surfaced[0]

    def test_notify_low_not_surfaced(self, brain_setup, tmp_dir):
        from event_bus import ChamehaEvent, EventType, Severity
        brain, _ = brain_setup
        surfaced = []
        brain.on_surface(lambda msg, e: surfaced.append(msg))

        event = ChamehaEvent(
            source     = "hal.sensors",
            event_type = EventType.NOTIFY,
            severity   = Severity.LOW,
            message    = "Sensor ping",
        )
        with patch("brain.AUDIT_DIR", str(tmp_dir / "audit")):
            brain._handle(event)

        assert len(surfaced) == 0

    def test_notify_critical_surfaces(self, brain_setup, tmp_dir):
        from event_bus import ChamehaEvent, EventType, Severity
        brain, _ = brain_setup
        surfaced = []
        brain.on_surface(lambda msg, e: surfaced.append(msg))

        event = ChamehaEvent(
            source     = "novela.risk",
            event_type = EventType.NOTIFY,
            severity   = Severity.CRITICAL,
            message    = "Patient critical",
        )
        with patch("brain.AUDIT_DIR", str(tmp_dir / "audit")):
            brain._handle(event)

        assert len(surfaced) == 1

    def test_deduplication(self, brain_setup, tmp_dir):
        from event_bus import ChamehaEvent, EventType, Severity
        brain, _ = brain_setup
        surfaced = []
        brain.on_surface(lambda msg, e: surfaced.append(msg))

        event = ChamehaEvent(
            source     = "sentinel.core",
            event_type = EventType.LOCK,
            severity   = Severity.CRITICAL,
            message    = "Same event repeated",
        )
        with patch("brain.AUDIT_DIR", str(tmp_dir / "audit")):
            brain._handle(event)
            # Second identical event within DEDUP_WINDOW -- should be suppressed
            event2 = ChamehaEvent(
                source     = "sentinel.core",
                event_type = EventType.LOCK,
                severity   = Severity.CRITICAL,
                message    = "Same event repeated",
            )
            brain._handle(event2)

        assert len(surfaced) == 1

    def test_ask_routes_to_callback(self, brain_setup, tmp_dir):
        from event_bus import ChamehaEvent, EventType, Severity
        brain, _ = brain_setup
        asked = []
        brain.on_ask(lambda e: asked.append(e))

        event = ChamehaEvent(
            source     = "byngox.health",
            event_type = EventType.ASK,
            severity   = Severity.HIGH,
            message    = "Confirm treatment?",
        )
        with patch("brain.AUDIT_DIR", str(tmp_dir / "audit")):
            brain._handle(event)

        assert len(asked) == 1

    def test_source_label_mapping(self, brain_setup, tmp_dir):
        brain, _ = brain_setup
        assert brain._source_label("sentinel.core")  == "Sentinel"
        assert brain._source_label("byngox.health")  == "Health Monitor"
        assert brain._source_label("novela.risk")    == "Health Risk"
        assert brain._source_label("unknown.source") == "Unknown"

    def test_audit_creates_file(self, brain_setup, tmp_dir):
        from event_bus import ChamehaEvent, EventType, Severity
        brain, _ = brain_setup
        event = ChamehaEvent(
            source     = "test",
            event_type = EventType.NOTIFY,
            severity   = Severity.LOW,
            message    = "audit test",
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

    def test_sealed_when_nodeid_found(self):
        from identity import DeviceIdentity
        with patch("builtins.open", mock_open(read_data="abc123\n")):
            identity = DeviceIdentity()
        assert identity.sealed  is True
        assert identity.node_id == "abc123"

    def test_not_sealed_when_missing(self):
        from identity import DeviceIdentity
        with patch("builtins.open", side_effect=FileNotFoundError):
            identity = DeviceIdentity()
        assert identity.sealed  is False
        assert identity.node_id is None

    def test_short_id(self):
        from identity import DeviceIdentity
        with patch("builtins.open", mock_open(read_data="abcdef123456789xyz")):
            identity = DeviceIdentity()
        assert len(identity.short_id()) == 12
        assert identity.short_id()      == "abcdef123456"

    def test_assert_sealed_raises_when_not_sealed(self):
        from identity import DeviceIdentity
        with patch("builtins.open", side_effect=FileNotFoundError):
            identity = DeviceIdentity()
        with pytest.raises(RuntimeError, match="NodeID not found"):
            identity.assert_sealed()

    def test_assert_sealed_passes_when_sealed(self):
        from identity import DeviceIdentity
        with patch("builtins.open", mock_open(read_data="nodeid123")):
            identity = DeviceIdentity()
        identity.assert_sealed()   # should not raise

    def test_not_sealed_when_permission_error(self):
        from identity import DeviceIdentity
        with patch("builtins.open", side_effect=PermissionError):
            identity = DeviceIdentity()
        assert identity.sealed is False


# ============================================================================
# UserConfig
# ============================================================================

class TestUserConfig:

    @pytest.fixture
    def config(self, tmp_dir):
        from identity import DeviceIdentity
        from config import UserConfig
        with patch("builtins.open", mock_open(read_data="test-node-id")):
            identity = DeviceIdentity()
        with patch.dict(os.environ, {"CHAMEHA_CONFIG_DIR": str(tmp_dir)}):
            c = UserConfig(identity)
        return c, identity, tmp_dir

    def test_default_first_boot(self, config):
        c, _, _ = config
        assert c.is_first_boot() is True
        assert c.name  == "friend"
        assert c.boots == 0

    def test_complete_first_boot(self, config):
        c, identity, tmp_dir = config
        with patch.dict(os.environ, {"CHAMEHA_CONFIG_DIR": str(tmp_dir)}):
            c.complete_first_boot("Jonah")
        assert c.name           == "Jonah"
        assert c.is_first_boot() is False
        assert c.boots           == 1

    def test_increment_boot(self, config):
        c, identity, tmp_dir = config
        with patch.dict(os.environ, {"CHAMEHA_CONFIG_DIR": str(tmp_dir)}):
            c.increment_boot()
            c.increment_boot()
        assert c.boots == 2

    def test_region_default(self, config):
        c, _, _ = config
        assert c.region == "KE"

    def test_node_id_mismatch_resets(self, tmp_dir):
        from identity import DeviceIdentity
        from config import UserConfig
        import json as _json

        # Write config with different node_id
        cfg_file = tmp_dir / "user.json"
        cfg_file.write_text(_json.dumps({
            "node_id":            "different-node",
            "name":               "Alice",
            "boots":              10,
            "first_boot_complete": True,
            "locale":             "sw",
            "region":             "KE",
        }))

        with patch("builtins.open", mock_open(read_data="my-actual-node")):
            identity = DeviceIdentity()
        with patch.dict(os.environ, {"CHAMEHA_CONFIG_DIR": str(tmp_dir)}):
            c = UserConfig(identity)

        # Should reset to defaults since node_id doesn't match
        assert c.is_first_boot() is True


# ============================================================================
# Tier 1 -- Language detection and model selection
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
        from tier1 import get_tier1
        with patch("urllib.request.urlopen", side_effect=Exception("offline")):
            a = get_tier1()
            b = get_tier1()
        assert a is b


# ============================================================================
# Tier 2 -- GPU detection and model selection
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
        from tier2 import get_tier2
        with patch("tier2._check_gpu", return_value=False):
            a = get_tier2()
            b = get_tier2()
        assert a is b


# ============================================================================
# Tier 3 -- Sanitization
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
        result = tier3._sanitize("Hash: deadbeef" * 5)
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
    def conv(self):
        from conversation import Conversation
        with patch("tier1.Tier1._check_ollama", return_value=False), \
             patch("tier2._check_gpu", return_value=False), \
             patch("tier3.Tier3._check_available", return_value=False):
            return Conversation()

    def test_cloud_empty_returns_usage(self, conv):
        result = conv.respond("/cloud")
        assert "Usage" in result

    def test_cloud_with_query_routes_tier3(self, conv):
        conv.tier3.respond = MagicMock(return_value="Tier 3 response")
        result = conv.respond("/cloud What is the latest research on malaria?")
        assert result == "Tier 3 response"

    def test_tier1_offline_fallback_message(self, conv):
        # Tier 1 offline, Tier 2 offline -- should return unavailable message
        result = conv.respond("Hello Chameha")
        assert "unavailable" in result.lower() or "model" in result.lower()

    def test_tier1_online_returns_response(self, conv):
        conv.tier1.available = True
        conv.tier1.chat      = MagicMock(return_value="I am here to help.")
        result = conv.respond("How are you?")
        assert result == "I am here to help."

    def test_complex_query_tries_tier2_first(self, conv):
        conv.tier2.available = True
        conv.tier2.chat      = MagicMock(return_value="Clinical tier 2 response")
        result = conv.respond("What are the symptoms and treatment protocol for severe malaria?")
        assert result == "Clinical tier 2 response"

    def test_status_returns_all_tiers(self, conv):
        s = conv.status()
        assert "tier1" in s
        assert "tier2" in s
        assert "tier3" in s

    def test_is_complex_long_query(self):
        from conversation import _is_complex
        long_query = "a" * 130
        assert _is_complex(long_query) is True

    def test_is_complex_clinical_keyword(self):
        from conversation import _is_complex
        assert _is_complex("What is the correct dosage for this patient?") is True

    def test_is_not_complex_short_casual(self):
        from conversation import _is_complex
        assert _is_complex("Hello how are you?") is False


# ============================================================================
# NATS Listener
# ============================================================================

class TestNatsListener:

    def test_dispatch_known_subject(self):
        from event_bus import EventBus
        from nats_listener import NatsListener
        bus      = EventBus()
        received = []
        bus.subscribe(lambda e: received.append(e))
        bus.start()

        listener = NatsListener(bus)
        payload  = json.dumps({
            "message":    "Threat contained",
            "confidence": 0.95,
        })
        listener._dispatch("sorabbyngo.sentinel.contained", payload)
        time.sleep(0.1)
        bus.stop()

        assert len(received) == 1
        assert received[0].source     == "sentinel.blue"
        assert received[0].confidence == 0.95

    def test_dispatch_unknown_subject_ignored(self):
        from event_bus import EventBus
        from nats_listener import NatsListener
        bus      = EventBus()
        received = []
        bus.subscribe(lambda e: received.append(e))
        bus.start()

        listener = NatsListener(bus)
        listener._dispatch("sorabbyngo.unknown.subject", '{"message":"x"}')
        time.sleep(0.1)
        bus.stop()

        assert len(received) == 0

    def test_dispatch_invalid_json_uses_raw(self):
        from event_bus import EventBus
        from nats_listener import NatsListener
        bus      = EventBus()
        received = []
        bus.subscribe(lambda e: received.append(e))
        bus.start()

        listener = NatsListener(bus)
        listener._dispatch("sorabbyngo.byngox.risk", "not-valid-json")
        time.sleep(0.1)
        bus.stop()

        assert len(received) == 1

    def test_process_buffer_extracts_message(self):
        from event_bus import EventBus
        from nats_listener import NatsListener
        bus      = EventBus()
        received = []
        bus.subscribe(lambda e: received.append(e))
        bus.start()

        listener  = NatsListener(bus)
        payload   = json.dumps({"message": "buffer test"})
        buf       = f'MSG sorabbyngo.byngox.risk 1 {len(payload)}\r\n{payload}\r\n'
        remaining = listener._process_buffer(buf)
        time.sleep(0.1)
        bus.stop()

        assert remaining == ""
        assert len(received) == 1


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
        greeting = t.get_greeting("Jonah")
        assert "Jonah" in greeting
        assert "Sorabbyngo" in greeting

    def test_get_greeting_without_name(self):
        from personality.tone_engine import ToneEngine
        t = ToneEngine()
        greeting = t.get_greeting()
        assert len(greeting) > 0

    def test_invalid_mode_ignored(self):
        from personality.tone_engine import ToneEngine
        t = ToneEngine()
        t.set_mode("nonexistent")
        assert t.current_mode == "patient"   # unchanged


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
        hint = get_response_language_hint("Good morning")
        assert "English" in hint

    def test_response_hint_swahili(self):
        from personality.language_detect import get_response_language_hint
        hint = get_response_language_hint("Habari yako daktari asante")
        assert "Swahili" in hint
