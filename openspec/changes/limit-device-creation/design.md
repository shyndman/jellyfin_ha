# Design: limit-device-creation

## Context

The device key (currently `{DeviceId}.{Client}`) flows through multiple components and is the primary identifier for device tracking, entity creation, and callback dispatch. Changing this key affects several interconnected systems.

## Device Key Usage Map

The device key is used in **6 locations** across 2 files:

### `__init__.py` — JellyfinClientManager

| Line | Usage | Description |
|------|-------|-------------|
| 522 | `_devices: Mapping[str, JellyfinDevice]` | Device tracking dict declaration |
| 753 | `dev_name = '{}.{}'.format(device['DeviceId'], device['Client'])` | **Key construction** — change here |
| 762 | `active_devices.append(dev_name)` | Tracks which devices are in current session list |
| 763-768 | `if dev_name not in self._devices` | New device detection + dict insertion |
| 786 | `self._do_update_callback(dev_name)` | Callback dispatch uses key |
| 794-795 | `self._do_update_callback(dev_id)` / `_do_stale_devices_callback(dev_id)` | Stale device callbacks use key |

### `media_player.py` — Callbacks & Entity

| Line | Usage | Description |
|------|-------|-------------|
| 55-56 | `active_jellyfin_devices: dict` / `inactive_jellyfin_devices: dict` | Local tracking dicts keyed by device key |
| 66-73 | `for dev_id in _jelly.devices` | Iterates manager's device dict |
| 91-93 | `if data in active_jellyfin_devices` | Stale callback receives device key as `data` |
| 108-109 | `self.device_id = device_id` / `self.jelly_cm.devices[self.device_id]` | Entity stores key, uses it to look up device |
| 118 | `add_update_callback(self.async_update_callback, self.device_id)` | Callback registration uses key |
| 122 | `remove_update_callback(self.async_update_callback, self.device_id)` | Callback deregistration uses key |
| 165 | `return self.device_id` | `unique_id` property returns the key |

## Device Lifecycle State Machine

```
                    ┌─────────────────────────────────────────┐
                    │                                         │
                    ▼                                         │
    Session      ┌──────────┐    session lost    ┌────────┐  │  session returns
    appears  ───▶│  ACTIVE  │ ──────────────────▶│  STALE │──┘
                 └──────────┘                    └────────┘
                      │                               │
                      │ _do_new_devices_callback()    │ _do_stale_devices_callback()
                      │ _do_update_callback()         │ _do_update_callback()
                      ▼                               ▼
                 [entity created]              [entity.available = False]
```

**State transitions in `update_device_list()`:**

1. **New device** (line 763-769): `dev_name not in self._devices` → create `JellyfinDevice`, add to dict, queue for callback
2. **Existing active** (line 770-786): Update session data, fire update callback if state changed
3. **Became inactive** (line 788-795): Device in dict but not in session list → mark inactive, fire stale callback
4. **Reactivated** (line 773-784): Was inactive, now in session list → fire new devices callback

## Callback System

Three callback types, all keyed by device key:

| Callback | Trigger | Handler Location |
|----------|---------|------------------|
| `_new_devices_callbacks` | New device or reactivated device | `media_player.py:62` — creates entity |
| `_stale_devices_callbacks` | Device no longer in session list | `media_player.py:89` — marks unavailable |
| `_update_callbacks` | Playback state change | `media_player.py:125` — updates HA state |

**Critical:** `_update_callbacks` stores `[callback, device_key]` pairs (line 1327). The key must match exactly for dispatch (line 1340).

## Filter Integration Point

The filter (`HasCustomDeviceName == true`) must be applied at **line 751** before any key construction or device tracking:

```python
for device in self._sessions:
    # NEW: Skip devices without custom names
    if not device.get('HasCustomDeviceName', False):
        continue

    # Existing logic continues with new key format...
    dev_name = '{}.{}'.format(device['DeviceName'], device['UserId'])
```

## Migration Considerations

**Breaking change:** Existing entities have `unique_id` = `{DeviceId}.{Client}`. After this change, the same physical device will have `unique_id` = `{DeviceName}.{UserId}`. Home Assistant will treat these as different entities.

Users will need to:
1. Delete old stale entities from the entity registry
2. Update automations/dashboards to reference new entity IDs

No code-level migration is needed — HA handles entity registry naturally.

## Risks

| Risk | Mitigation |
|------|------------|
| `DeviceName` or `UserId` missing from session | Use `.get()` with filter, log warning |
| Same DeviceName for different users | Key includes UserId, so unique per user |
| Callback mismatch after key format change | All 6 locations updated atomically |
