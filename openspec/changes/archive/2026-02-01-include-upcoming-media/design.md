# Design: Upcoming/YAMC user selection

## Current Situation
- Config flow validates URL/API key in a single `async_step_user` form. Upcoming/YAMC checkboxes appear immediately with defaults `False`.
- Runtime code in `JellyfinClientManager.update_data` calls Jellyfin endpoints with parameters containing `{UserId}` placeholders. The underlying client only replaces those placeholders when `config.data['auth.user_id']` is set, but `/Users/Me` never returns data for API-key auth, so the placeholders leak into outbound requests.

## Proposed Flow
1. **Step 1 – Connection**: Keep existing fields (URL, API key, verify SSL). After `_test_connection` succeeds, cache the authenticated client/context on the handler so it can be reused.
2. **Step 2 – Feature Options**: Present Upcoming/YAMC toggles. When the admin enables either toggle, show a dropdown populated from `client.jellyfin.get_public_users()` (fallback to `get_users()` when needed). Selecting an entry stores its `Id`.
3. **Options Flow** mirrors these steps so existing installations can add/change the user later.
4. **Runtime**: Store the chosen id under a new constant (e.g., `CONF_LIBRARY_USER_ID`). `JellyfinClientManager` reads it and injects the literal id into the query params instead of `{UserId}`. If the flags are enabled but no id exists (legacy entries), log a WARN, skip the API call, and surface a persistent notification guiding the admin to rerun options.

## Edge Cases & Validation
- API key must have rights to list users; if fetching fails, show a form error explaining that Upcoming/YAMC require an admin-level key.
- If the server has many users, cap the dropdown to names + friendly description (e.g., `"Display Name (username)"`).
- Store user ids as strings; no attempt to map names to ids at runtime.
