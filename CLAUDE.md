# CLAUDE.md - AI Assistant Guide for jellyfin_ha

## Project Overview

This is a **Home Assistant custom component** that provides integration with Jellyfin media servers. It's a forked version updated for compatibility with Home Assistant 2025.1+.

- **Domain**: `jellyfin`
- **Version**: 1.1.2
- **Python Dependency**: `jellyfin-apiclient-python==1.7.2`
- **IoT Class**: `local_push` (WebSocket-based real-time updates)

## Repository Structure

```
jellyfin_ha/
├── custom_components/jellyfin/   # Main integration code
│   ├── __init__.py              # Core integration setup, JellyfinClientManager
│   ├── config_flow.py           # Config/options flow for UI setup
│   ├── const.py                 # Constants, domain definitions, playlists
│   ├── media_player.py          # Media player entity implementation
│   ├── media_source.py          # Media source for browsing/casting
│   ├── sensor.py                # Server sensor entity
│   ├── services.yaml            # Service definitions
│   ├── strings.json             # UI strings (English base)
│   ├── manifest.json            # Integration manifest
│   └── translations/            # Localization files (de, en, fr)
├── changelog/changelog.md       # Version history
├── .github/workflows/validate.yaml  # HACS validation CI
├── hacs.json                    # HACS configuration
├── README.md                    # User documentation
└── LICENSE                      # GPL-3.0 license
```

## Architecture & Key Components

### Core Classes

#### `JellyfinClientManager` (`__init__.py:502`)
The central manager class that handles:
- Jellyfin server connection and authentication
- WebSocket event handling for real-time updates
- Device session tracking
- Media streaming URL generation
- Data updates for Upcoming/YAMC cards

#### `JellyfinDevice` (`__init__.py:242`)
Represents a Jellyfin playback device/session with properties for:
- Playback state (playing, paused, idle, off)
- Current media info (title, position, runtime, artwork)
- Remote control commands (play, pause, seek, etc.)

### Entity Platforms

| Platform | Entity | Purpose |
|----------|--------|---------|
| `sensor` | `JellyfinSensor` | Server status, upcoming media data |
| `media_player` | `JellyfinMediaPlayer` | Device playback control |

### Services

Defined in `services.yaml` and registered in `__init__.py:111-118`:

| Service | Target | Description |
|---------|--------|-------------|
| `trigger_scan` | sensor | Trigger Jellyfin library scan |
| `browse` | media_player | Display item info on device |
| `delete` | sensor | Delete media from library |
| `search` | sensor | Search media items |
| `yamc_setpage` | sensor | Set YAMC card page |
| `yamc_setplaylist` | sensor | Set YAMC card playlist |

### Media Source Integration

`media_source.py` provides:
- Library browsing via `BrowseMediaSource`
- Stream URL resolution for casting (Chromecast, etc.)
- Media type mapping (Movie, Episode, Audio, etc.)

## Development Workflows

### Installation for Development

1. Clone to `custom_components/jellyfin` in your HA config directory
2. Restart Home Assistant
3. Add integration via UI (Settings > Integrations > Add Integration > Jellyfin)

### CI/CD

- **HACS Validation**: Runs on push, PR, and daily schedule via `.github/workflows/validate.yaml`
- Uses `hacs/action@main` for integration category validation

### Testing Changes

No automated test suite exists. Testing is manual:
1. Install in HA development instance
2. Configure integration with test Jellyfin server
3. Verify entities appear and function correctly
4. Check Home Assistant logs for errors

## Code Conventions

### Imports

```python
# Standard library first
import logging
from typing import ...

# Third-party
import voluptuous as vol

# Home Assistant
from homeassistant.core import HomeAssistant
from homeassistant.components.media_player import ...

# Local
from . import JellyfinClientManager
from .const import DOMAIN, ...
```

### Logging

- Use module-level logger: `_LOGGER = logging.getLogger(__name__)`
- Debug logging for state changes and API calls
- Error logging for connection/API failures
- `autolog()` helper function for tracing entry/exit points

### Async Patterns

- Use `hass.async_add_executor_job()` for blocking Jellyfin API calls
- Entity callbacks use `@callback` decorator
- Platform setup via `async_setup_entry()`

### Entity Properties

Entities use `@property` decorators for state attributes:
```python
@property
def state(self):
    """Return the state of the device."""
    ...
```

### Config Entry Data

Configuration stored in `config_entry.data`:
- `CONF_URL`: Server URL
- `CONF_USERNAME`, `CONF_PASSWORD`: Credentials
- `CONF_VERIFY_SSL`: SSL verification flag
- `CONF_CLIENT_ID`: Unique client UUID
- `CONF_GENERATE_UPCOMING`, `CONF_GENERATE_YAMC`: Feature flags

## Common Patterns

### Adding a New Service

1. Add constant to `const.py`:
   ```python
   SERVICE_NEW = "new_service"
   ```

2. Add schema in `__init__.py`:
   ```python
   NEW_SERVICE_SCHEMA = SERVICE_SCHEMA.extend({...})
   ```

3. Register in `SERVICE_TO_METHOD`:
   ```python
   SERVICE_NEW: {'method': 'async_new_service', 'schema': NEW_SERVICE_SCHEMA},
   ```

4. Add service definition to `services.yaml`

5. Implement method in appropriate entity class

### Adding Entity Attributes

For sensor extra attributes, modify `JellyfinSensor.extra_state_attributes` in `sensor.py:87-99`.

### Media Type Mapping

Use the type mapping functions in `media_source.py`:
- `Type2Mediatype()` - Jellyfin type to HA MediaType
- `Type2Mediaclass()` - Jellyfin type to HA MediaClass
- `Type2Mimetype()` - Jellyfin type to MIME type
- `IsPlayable()` - Determine if type is directly playable

## Troubleshooting

### Common Issues

1. **Connection failures**: Check URL format, SSL settings, port (default 8096)
2. **WebSocket disconnects**: The manager auto-reconnects with exponential backoff
3. **Missing devices**: Devices appear only when actively playing or connected
4. **Entity disabled by default**: Media player entities are disabled by default (`_attr_entity_registry_enabled_default = False`)

### Debug Logging

Add to `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.jellyfin: debug
```

## Important Notes for AI Assistants

1. **This is a HACS custom component**, not core Home Assistant code
2. **Real-time updates** via WebSocket - do not add polling
3. **Media player entities disabled by default** - intentional design choice
4. **No test suite** - validate changes manually
5. **Translations** - update all language files in `translations/` when adding strings
6. **Version bumps** - update both `manifest.json` and document in `changelog/changelog.md`
7. **HACS compatibility** - ensure `hacs.json` and `manifest.json` stay valid

## External Documentation

- [Home Assistant Integration Development](https://developers.home-assistant.io/docs/creating_component_index)
- [HACS Custom Repositories](https://hacs.xyz/docs/faq/custom_repositories)
- [Jellyfin API](https://api.jellyfin.org/)
- [jellyfin-apiclient-python](https://github.com/jellyfin/jellyfin-apiclient-python)

<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->
