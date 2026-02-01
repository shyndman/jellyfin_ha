## ADDED Requirements

### Requirement: Custom Device Name Filter
The system SHALL only create Home Assistant media_player entities for Jellyfin sessions where `HasCustomDeviceName` is `true`.

#### Scenario: Device with custom name
- **WHEN** a Jellyfin session has `HasCustomDeviceName == true`
- **THEN** a media_player entity SHALL be created for that device

#### Scenario: Device without custom name
- **WHEN** a Jellyfin session has `HasCustomDeviceName == false`
- **THEN** no media_player entity SHALL be created for that device

### Requirement: Stable Device Identity
The system SHALL use the combination of `DeviceName` and `UserId` as the stable identifier for media_player entities.

#### Scenario: Entity unique_id format
- **WHEN** a media_player entity is created
- **THEN** its `unique_id` SHALL be `{DeviceName}.{UserId}`

#### Scenario: Re-authentication preserves identity
- **WHEN** a device re-authenticates with Jellyfin (generating a new DeviceId)
- **AND** the device has the same `DeviceName` and `UserId`
- **THEN** the existing media_player entity SHALL be updated (not duplicated)
