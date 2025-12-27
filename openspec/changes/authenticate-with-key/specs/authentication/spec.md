# Authentication

## ADDED Requirements

### Requirement: API Key Authentication

The integration SHALL authenticate with the Jellyfin server using an API key instead of username/password credentials.

#### Scenario: Successful authentication with valid API key
- **WHEN** user provides a valid Jellyfin API key and server URL
- **THEN** the integration authenticates successfully
- **AND** creates a connection to the Jellyfin server

#### Scenario: Failed authentication with invalid API key
- **WHEN** user provides an invalid API key
- **THEN** the integration fails to authenticate
- **AND** displays an appropriate error message

### Requirement: API Key Configuration

The config flow SHALL collect an API key from the user instead of username and password.

#### Scenario: Config flow shows API key field
- **WHEN** user adds the Jellyfin integration
- **THEN** the configuration form displays an "API Key" field
- **AND** does NOT display username or password fields

#### Scenario: Options flow shows API key field
- **WHEN** user edits the Jellyfin integration options
- **THEN** the options form displays the current API key
- **AND** allows the user to update it

### Requirement: Test Connection Button

The config flow SHALL provide a button to test the API key before saving the configuration.

#### Scenario: Test connection succeeds
- **WHEN** user clicks the "Test Connection" button with valid credentials
- **THEN** the integration attempts to connect to the server
- **AND** displays a success message

#### Scenario: Test connection fails
- **WHEN** user clicks the "Test Connection" button with invalid credentials
- **THEN** the integration attempts to connect to the server
- **AND** displays a failure message

## REMOVED Requirements

### Requirement: Username/Password Authentication
**Reason**: Replaced by API key authentication for improved security and simplicity.
**Migration**: Users must reconfigure the integration with an API key from their Jellyfin server.

### Requirement: Device ID Generation
**Reason**: API key authentication does not require a device ID - the key itself identifies the client.
**Migration**: None required - device ID was only used internally for authentication.
