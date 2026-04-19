# ADB Logcat Events

Custom Home Assistant component that captures **volume+** and **volume−** button presses from the Nvidia Android TV remote via ADB logcat, and exposes them as HA events usable in automations.

## Prerequisites

- **ADB debugging enabled** on the Android TV  
  `Settings → Device Preferences → Developer options → Network debugging`
- Home Assistant 2023.1+
- HACS installed

## Installation via HACS

1. HACS → Integrations → ⋮ → Custom repositories
2. Add the repository URL, category **Integration**
3. Install **ADB Logcat Events**
4. Restart Home Assistant

## Configuration

Settings → Devices & Services → Add integration → **ADB Logcat Events**

- **Name**: free label (e.g. `Android TV Living Room`)
- **IP**: IP address of the Android TV
- **Port**: `5555` (ADB default)

On first connection, **accept the ADB authorization prompt** displayed on the Android TV.

## HA Event

Each volume button press fires the `adb_logcat_events_button` event:

```yaml
event_type: adb_logcat_events_button
event_data:
  device_name: "Android TV Living Room"
  entry_id: "abc123..."
  action: volume_up   # or volume_down
```

## Example Automation

```yaml
alias: "Android Living Room - Volume → Amplifier"
trigger:
  - platform: event
    event_type: adb_logcat_events_button
    event_data:
      device_name: "Android TV Living Room"
      action: volume_up
    id: volume_up
  - platform: event
    event_type: adb_logcat_events_button
    event_data:
      device_name: "Android TV Living Room"
      action: volume_down
    id: volume_down
action:
  - choose:
      - conditions:
          - condition: trigger
            id: volume_up
        sequence:
          - service: media_player.volume_set
            target:
              entity_id: media_player.living_room_amp
            data:
              volume_level: >-
                {{ [state_attr('media_player.living_room_amp', 'volume_level') + 0.02, 1.0] | min }}
      - conditions:
          - condition: trigger
            id: volume_down
        sequence:
          - service: media_player.volume_set
            target:
              entity_id: media_player.living_room_amp
            data:
              volume_level: >-
                {{ [state_attr('media_player.living_room_amp', 'volume_level') - 0.02, 0.0] | max }}
mode: queued
max: 5
```

## Technical Notes

- The ADB key is generated automatically and stored in `/config/.storage/adb_logcat_events_adb_key`
- On network loss, automatic reconnection with exponential backoff (5s → 10s → 20s … max 5 min)
- Multi-device support: add one entry per Android TV
- Does not interfere with the **Android TV Remote** integration (distinct protocols)
