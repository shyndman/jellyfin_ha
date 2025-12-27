## 1. Implementation

- [x] 1.1 Update `JellyfinDevice` to store `DeviceName`, `UserId`, and `HasCustomDeviceName` from session data
  - Already stored in session; no changes needed
- [x] 1.2 Change `JellyfinDevice.unique_id` to return `{UserId}{DeviceName}` format
  - Not needed; unique_id comes from the device key passed to JellyfinMediaPlayer
- [x] 1.3 Update `JellyfinClientManager.update_device_list()` to filter out sessions where `HasCustomDeviceName == false`
  - Added filter at `__init__.py:754`
- [x] 1.4 Update device tracking dict key from `{DeviceId}.{Client}` to `{UserId}{DeviceName}`
  - Changed at `__init__.py:768`
- [x] 1.5 Update `JellyfinMediaPlayer.unique_id` to use the new stable identifier
  - Already returns `self.device_id` which is the device key
- [x] 1.6 Update callback registration to use new device key format
  - Automatically uses the same device key throughout

## 2. Validation

- [ ] 2.1 Test with TV session (HasCustomDeviceName=true) — entity created
- [ ] 2.2 Test with browser session (HasCustomDeviceName=false) — no entity created
- [ ] 2.3 Test re-authentication — same entity updated, no duplicate
