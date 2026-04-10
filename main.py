"""
main.py — Chameha entry point
Called by sorabbyngo-init on boot
ADR-009 enforced: Tier 1 default, Tier 3 explicit /cloud only
"""

import os
import sys
import time

from identity import DeviceIdentity
from config import UserConfig
from event_bus import EventBus, Severity
from brain import Brain
from nats_listener import NatsListener
from conversation import Conversation


# ------------------------------------------------------------------
# Boot UI
# ------------------------------------------------------------------

def print_banner(identity: DeviceIdentity):
    print("")
    print("  ╔═══════════════════════════════════════════╗")
    print("  ║       SORABBYNGO OS — CHAMEHA             ║")
    print("  ║       Rhythm of Digital Life              ║")
    print("  ╚═══════════════════════════════════════════╝")
    print(f"  Node   : {identity.short_id()}...")
    print(f"  Kernel : {os.uname().release}")
    print("")


def first_boot(config: UserConfig, conv: Conversation):
    print("  First boot detected.")
    print("")
    try:
        name = input("  What is your name? ").strip()
    except (EOFError, KeyboardInterrupt):
        name = "friend"

    if not name:
        name = "friend"

    config.complete_first_boot(name)
    print("")

    # Tier 1 welcome — local, no consent needed, no network
    response = conv.respond(
        f"Welcome the user {name} on their first boot of Sorabbyngo OS. "
        f"Two sentences. Mention NodeID-sealed and Africa-first."
    )
    print(f"  {response}")
    print("")


def normal_boot(config: UserConfig, conv: Conversation):
    hour = int(time.strftime("%H"))
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    config.increment_boot()
    print(f"  {greeting}, {config.name}. Boot #{config.boots}.")

    # Tier 1 — local greeting, no API call
    response = conv.respond(
        f"One warm sentence greeting {config.name} on boot number {config.boots}."
    )
    print(f"  {response}")
    print("")


# ------------------------------------------------------------------
# Event display — Brain calls this when something surfaces
# ------------------------------------------------------------------

def on_event_surfaced(message: str, event):
    print(message)
    print("")


# ------------------------------------------------------------------
# Conversation loop — persistent service
# ------------------------------------------------------------------

def conversation_loop(config: UserConfig, brain: Brain, conv: Conversation):
    print("  Commands: status | /cloud <query> | exit")
    print("  All responses are local by default. /cloud for external intelligence.\n")

    while True:
        try:
            user_input = input(f"  {config.name}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Dropping to shell.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "shell"):
            print("  Dropping to shell.")
            break

        if user_input.lower() == "status":
            tier_status = conv.status()
            print("")
            print(f"  NodeID    : {config.data.get('node_id', 'unknown')[:16]}...")
            print(f"  Kernel    : {os.uname().release}")
            print(f"  Boot #    : {config.boots}")
            print(f"  Tier 1    : {tier_status['tier1']}")
            print(f"  Tier 3    : {tier_status['tier3']} (explicit /cloud only)")
            print(f"  NATS      : sorabbyngo.* subscribed")
            print(f"  Sentinel  : active")
            print("")
            continue

        # Route through Conversation — Tier 1 default, Tier 3 on /cloud only
        response = conv.respond(user_input)
        print(f"\n  Chameha: {response}\n")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    # 1. Device identity
    identity = DeviceIdentity()
    try:
        identity.assert_sealed()
    except RuntimeError as e:
        print(f"  [warn] {e} — running in degraded mode")

    # 2. User config
    config = UserConfig(identity)

    # 3. Conversation router — Tier 1 + Tier 3
    conv = Conversation()

    # 4. Event bus
    bus = EventBus()
    bus.start()

    # 5. Brain
    brain = Brain(bus, identity, config)
    brain.on_surface(on_event_surfaced)

    # 6. NATS listener
    nats = NatsListener(bus)
    nats.start()

    # 7. Boot UI
    print_banner(identity)

    if config.is_first_boot():
        first_boot(config, conv)
    else:
        normal_boot(config, conv)

    # 8. Persistent conversation loop
    conversation_loop(config, brain, conv)

    # 9. Drop to shell
    os.execv("/bin/sh", ["/bin/sh"])


if __name__ == "__main__":
    main()
