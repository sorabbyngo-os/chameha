# Remote Device Control

Remote control is implemented through AION.

Flow

User
↓

Chameha
↓

AION

↓

Capability Broker

↓

Device Agent

↓

Target Device

AION never executes privileged operations directly.

Every operation passes through the capability broker.

Examples

- open application
- lock screen
- send file
- control phone
- reboot
- sleep
- power management
- clipboard
- notifications
