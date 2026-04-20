# Gateway Firmware Rollout

Firmware releases for HelioHome gateway hubs are staged in three rings.

## Ring 1

- Team homes
- Demo apartments
- Internal lab racks

## Ring 2

- Pilot customers with fewer than six devices
- No homes with electronic door access

## Ring 3

- General customer base

Rollback triggers:

- Hub reboot loop detected twice in 30 minutes.
- Thermostat automations delayed by more than five minutes.
- Lock telemetry missing for more than one polling cycle.