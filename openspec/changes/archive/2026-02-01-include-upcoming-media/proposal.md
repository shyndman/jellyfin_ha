# Change: Include Upcoming/YAMC media with explicit Jellyfin user selection

## Why
Upcoming and YAMC data queries still inject the literal string `{UserId}` because API-key authentication never returns a Jellyfin user id via `/Users/Me`. The integration now attempts that call, logs an error, and aborts setup because the endpoint will never yield an Id for an API key. We need a supported way to bind those optional features to a specific Jellyfin user.

## What Changes
- Split the config/options flow into two stages so the Jellyfin connection is validated first, then the optional Upcoming/YAMC toggles are shown.
- When either toggle is enabled, require the admin to choose a Jellyfin user (populated from the server’s user list) whose id will power the data queries.
- Persist that user id in the config entry and plumb it into the existing Upcoming/YAMC helpers so the Jellyfin API receives a valid `UserId`.
- Surface migrations/guards so existing entries either disable the features or prompt for a user id during options flow.

## Impact
- Affects Home Assistant config flow (`custom_components/jellyfin/config_flow.py`) and related translation strings.
- Touches sensor/upcoming logic in `custom_components/jellyfin/__init__.py` and `sensor.py` to consume the stored user id.
- Requires new config constants plus tests/validation around user selection.
