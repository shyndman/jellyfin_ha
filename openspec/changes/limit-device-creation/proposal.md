# Change: Limit Device Entity Creation to Custom-Named Devices

## Why

Jellyfin web clients (including smart TVs) generate DeviceId values that include a login timestamp, causing a new DeviceId on every re-authentication. This results in entity proliferation, broken automations/dashboards, and no stable way to reference physical devices.

## What Changes

- **Filter**: Only create entities when `HasCustomDeviceName == true`
- **Identity**: Use `{DeviceName}.{UserId}` as `unique_id` instead of `{DeviceId}.{Client}`
- **Ignore**: Sessions without custom device names produce no HA entities

## Impact

- Affected specs: device-management (new)
- Affected code: `custom_components/jellyfin/__init__.py`, `custom_components/jellyfin/media_player.py`
- **BREAKING**: Existing entities will get new unique_ids; users may need to update automations/dashboards once
