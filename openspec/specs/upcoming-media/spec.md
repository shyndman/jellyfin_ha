# upcoming-media Specification

## Purpose
TBD - created by archiving change include-upcoming-media. Update Purpose after archive.
## Requirements
### Requirement: Setup flow collects feature user when Upcoming/YAMC enabled
The Home Assistant config and options flows SHALL present Upcoming and YAMC toggles only after the Jellyfin connection succeeds and SHALL require the admin to select a Jellyfin user id whenever either toggle is enabled.

#### Scenario: Successful selection
- **GIVEN** the admin enters valid server credentials
- **WHEN** they enable Upcoming media and pick a user from the dropdown
- **THEN** the config entry stores the connection details, the enabled flag(s), and the selected user id.

#### Scenario: Missing user
- **GIVEN** the admin enables either Upcoming or YAMC
- **WHEN** they attempt to continue without selecting a user
- **THEN** the flow displays a validation error explaining that a Jellyfin user is required.

### Requirement: Upcoming/YAMC use stored user id
When Upcoming or YAMC generation is enabled, the integration SHALL inject the stored user id into all Jellyfin API calls powering those features and SHALL refuse to call those endpoints if no user id is configured.

#### Scenario: Valid id
- **GIVEN** a config entry with Upcoming enabled and a stored user id
- **WHEN** the integration refreshes Upcoming or YAMC data
- **THEN** the Jellyfin requests include the stored id (never `{UserId}` literals) and the returned data is attached to the sensor attributes.

#### Scenario: Legacy entry without user id
- **GIVEN** an existing config entry where Upcoming or YAMC is enabled but no user id exists
- **WHEN** the integration attempts to refresh feature data
- **THEN** it logs a warning, skips the API calls, and prompts the admin to edit the integration to select a user.

