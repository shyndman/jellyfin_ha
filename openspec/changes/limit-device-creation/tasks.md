## 1. Implementation

- [ ] 1.1 Update `JellyfinDevice` to store `DeviceName`, `UserId`, and `HasCustomDeviceName` from session data
- [ ] 1.2 Change `JellyfinDevice.unique_id` to return `{DeviceName}.{UserId}` format
- [ ] 1.3 Update `JellyfinClientManager.update_device_list()` to filter out sessions where `HasCustomDeviceName == false`
- [ ] 1.4 Update device tracking dict key from `{DeviceId}.{Client}` to `{DeviceName}.{UserId}`
- [ ] 1.5 Update `JellyfinMediaPlayer.unique_id` to use the new stable identifier
- [ ] 1.6 Update callback registration to use new device key format

## 2. Validation

- [ ] 2.1 Test with TV session (HasCustomDeviceName=true) — entity created
- [ ] 2.2 Test with browser session (HasCustomDeviceName=false) — no entity created
- [ ] 2.3 Test re-authentication — same entity updated, no duplicate
