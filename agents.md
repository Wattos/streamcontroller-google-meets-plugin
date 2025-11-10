# Agent Guide - Google Meet StreamController Plugin

This document provides context for AI agents working on this codebase. It describes the architecture, patterns, conventions, and key concepts needed to make changes effectively.

## Project Overview

A StreamController plugin that controls Google Meet from a Stream Deck via a Chrome extension. Features include toggling mic/camera, raising hand, and sending reactions with real-time state synchronization.

**Key Constraint**: Uses WebSocket communication instead of keyboard shortcuts for reliable state synchronization.

## Architecture Pattern

### Three-Layer Architecture

```
[StreamController Actions] <--Pyro--> [Backend] <--Method Calls--> [GoogleMeetsController]
         (Frontend)                    (Wrapper)                    (WebSocket Server)
                                                                            |
                                                                            v
                                                                    [Chrome Extension]
```

1. **Actions** (Frontend): User-facing buttons on Stream Deck
   - Extend `GoogleMeetActionBase`
   - Call backend methods via Pyro RPC
   - Update UI based on state
   - Run in StreamController's main process

2. **Backend**: API wrapper running in separate process
   - Extends `BackendBase` from `streamcontroller-plugin-tools`
   - Exposes simple methods to actions
   - Forwards commands to controller
   - Manages settings persistence

3. **GoogleMeetsController**: WebSocket server
   - Runs async event loop in background thread
   - Handles WebSocket connections from Chrome extension
   - Manages authentication, state, and commands
   - All networking logic lives here

### Why This Separation?

- **Backend vs Controller separation**: Backend handles Pyro serialization, settings, and provides synchronous API. Controller handles all async/networking complexity.
- **No networking in actions**: Actions never touch WebSocket code directly
- **Single responsibility**: Each layer has one job

## Key Files

### Core Files

- **`main.py`**: Plugin registration and action holders
  - Class: `GoogleMeetPlugin(PluginBase)`
  - Launches backend via `self.launch_backend()`
  - Registers 4 actions with input support

- **`backend/backend.py`**: Backend wrapper (runs in separate process)
  - Class: `Backend(BackendBase)`
  - Methods: `toggle_microphone()`, `toggle_camera()`, `toggle_hand()`, `send_reaction()`
  - State queries: `get_mic_enabled()`, `get_camera_enabled()`, etc.
  - Settings management for approved extensions

- **`backend/GoogleMeetsController.py`**: WebSocket server
  - Class: `GoogleMeetsController`
  - Async WebSocket server on localhost:8765
  - HMAC authentication with ephemeral session keys
  - State tracking and command forwarding
  - Extension approval workflow

### Action Files

- **`GoogleMeetActionBase.py`**: Base class for all actions
  - Connection checking: `get_connected()`, `get_in_meeting()`
  - Error handling: `show_error()`
  - Config UI: WebSocket port settings
  - Status label management

- **`actions/mixins/MixinBase.py`**: State management pattern
  - `State` enum: UNKNOWN (-1), DISABLED (0), ENABLED (1)
  - Abstract `next_state()` method
  - Used for toggle actions

- **`actions/mixins/ToggleMixin.py`**: Toggle behavior
  - Implements `next_state()` for ENABLED ↔ DISABLED

- **`actions/ToggleMic/ToggleMic.py`**: Microphone toggle action
- **`actions/ToggleCamera/ToggleCamera.py`**: Camera toggle action
- **`actions/RaiseHand/RaiseHand.py`**: Hand raise/lower action
- **`actions/SendReaction/SendReaction.py`**: Reaction sender (non-toggle)

## Patterns & Conventions

### 1. Action Pattern

All toggle actions follow this structure:

```python
class ToggleMic(ToggleMixin, GoogleMeetActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_state = State.UNKNOWN
        self.image_path_map = {
            State.UNKNOWN: "error.png",
            State.ENABLED: "mic_on.png",
            State.DISABLED: "mic_off.png",
        }

    def on_ready(self):
        # Start state update thread
        threading.Thread(target=self.update_state, daemon=True).start()

    def update_state(self):
        # Query backend for current state
        # Update self.current_state
        # Call show_for_state()

    def show_for_state(self, state: State):
        # Update icon and label based on state
        # Only update if state changed

    def on_key_down(self):
        # Send command to backend
        # Schedule delayed state update

    def on_tick(self):
        # Called periodically by StreamController
        # Update state from backend
```

**Important**:
- `update_state()` runs in background thread
- `show_for_state()` only updates UI if state changed
- `on_tick()` provides periodic state sync (hybrid approach)

### 2. Backend Method Pattern

```python
def toggle_microphone(self) -> bool:
    """Toggle microphone. Returns True if command sent."""
    try:
        self.controller.toggle_microphone()
        return True
    except Exception as e:
        LOG.error(f"Error: {e}")
        return False
```

All backend methods:
- Return `bool` for success/failure OR state data
- Handle exceptions and log errors
- Forward to controller methods

### 3. Controller Command Pattern

```python
def toggle_microphone(self):
    """Toggle microphone in meeting"""
    if self.loop:
        asyncio.run_coroutine_threadsafe(
            self.send_command("toggle_mic"),
            self.loop
        )
```

Controller provides sync methods that schedule async WebSocket sends.

### 4. WebSocket Message Format

All messages are JSON with this structure:

```json
{
  "type": "command|state|handshake|heartbeat",
  "action": "toggle_mic|toggle_camera|toggle_hand|send_reaction",
  "data": {},
  "hmac": "sha256_signature"
}
```

**Handshake flow**:
1. Extension → `{"type": "handshake", "extension_id": "xxx"}`
2. Server checks approval (requests if needed)
3. Server → `{"type": "handshake_success", "session_key": "xxx"}`
4. All subsequent messages include HMAC signature

**State update**:
```json
{
  "type": "state",
  "data": {
    "mic_enabled": true,
    "camera_enabled": false,
    "hand_raised": false,
    "in_meeting": true,
    "meeting_id": "abc-def-ghi"
  },
  "hmac": "..."
}
```

### 5. Settings Storage

Settings stored in plugin settings JSON:

```python
settings = self.plugin_base.get_settings()
settings["websocket_port"] = 8765
settings["approved_extensions"] = ["extension_id_1", "extension_id_2"]
self.plugin_base.set_settings(settings)
```

## Module Import Paths

**Critical**: Action imports use the plugin directory name (NOT the plugin ID):

```python
# In actions
from plugins.github_wattos_google_meets_plugin.GoogleMeetActionBase import GoogleMeetActionBase
from plugins.github_wattos_google_meets_plugin.actions.mixins import ToggleMixin, State
```

**Plugin Directory**: `github_wattos_google_meets_plugin`
**Plugin ID**: `com_github_wattos_google_meet` (from manifest.json)

**Important**: StreamController uses the actual directory name for imports, not the plugin ID!

## Threading Model

### Backend (separate process)

- **Main thread**: Handles Pyro RPC calls from actions
- **WebSocket thread**: Runs async event loop for WebSocket server
  - Started in `GoogleMeetsController.start()`
  - Uses `asyncio.run_coroutine_threadsafe()` to schedule commands

### Actions (StreamController process)

- **Main thread**: GTK event loop, UI updates
- **Background threads**: State updates, delayed operations
  - Always use `daemon=True`
  - Keep short-lived (no long-running loops)
  - Use `on_tick()` for periodic updates instead

## Error Handling

### Connection Errors

Actions check connection before operations:

```python
if not self.get_connected():
    self.show_error()
    return

if not self.get_in_meeting():
    self.set_bottom_label("No Meeting", font_size=12)
    return
```

### State Errors

If backend returns `None`:
```python
mic_enabled = self.plugin_base.backend.get_mic_enabled()
if mic_enabled is None:
    self.current_state = State.UNKNOWN
    self.show_error()
    return
```

### WebSocket Errors

Controller methods catch exceptions:
```python
try:
    await self.active_connection.send(json.dumps(command))
    return True
except Exception as e:
    log.error(f"Error sending command: {e}")
    return False
```

## Security Considerations

### HMAC Authentication

1. Handshake exchanges session key (ephemeral, per-connection)
2. All non-handshake messages require HMAC signature
3. Signature computed on message without `hmac` field:
   ```python
   message_str = json.dumps(message, sort_keys=True)
   signature = hmac.new(key.encode(), message_str.encode(), hashlib.sha256).hexdigest()
   ```

### Extension Approval

- Extensions must be approved before connecting
- Approval requested via `request_approval()` → creates Future
- UI (not yet implemented) should call `approve_extension()` or `deny_extension()`
- Approved extensions stored in plugin settings
- Can revoke via `revoke_extension()` (disconnects active connection)

### Localhost Only

WebSocket server binds to `127.0.0.1` only - no external connections.

## Assets & Icons

Icons located in `assets/`:
- `mic_on.png`, `mic_off.png`
- `camera_on.png`, `camera_off.png`
- `hand_raised.png`, `hand_lowered.png`
- `error.png` - shown when connection fails
- `reaction.png` - generic reaction fallback
- `reactions/` subdirectory with emoji icons

**Current state**: All placeholder copies of `info.png`
**TODO**: Replace with proper icons (see `assets/ASSETS_NEEDED.md`)

## Testing Without Chrome Extension

### Mock WebSocket Client

Create a test client to simulate the extension:

```python
import asyncio
import websockets
import json
import hmac
import hashlib

async def test_client():
    uri = "ws://127.0.0.1:8765"
    async with websockets.connect(uri) as ws:
        # Handshake
        await ws.send(json.dumps({
            "type": "handshake",
            "extension_id": "test_extension_123"
        }))

        response = json.loads(await ws.recv())
        session_key = response["session_key"]

        # Send state update
        state = {
            "type": "state",
            "data": {
                "mic_enabled": True,
                "camera_enabled": False,
                "hand_raised": False,
                "in_meeting": True,
                "meeting_id": "test-meeting"
            }
        }
        state_str = json.dumps(state, sort_keys=True)
        state["hmac"] = hmac.new(
            session_key.encode(),
            state_str.encode(),
            hashlib.sha256
        ).hexdigest()
        await ws.send(json.dumps(state))

        # Listen for commands
        async for message in ws:
            data = json.loads(message)
            print(f"Received: {data}")

asyncio.run(test_client())
```

## Common Tasks

### Adding a New Action

1. Create directory: `actions/NewAction/`
2. Create `NewAction.py`:
   - Extend `GoogleMeetActionBase`
   - Optionally use `ToggleMixin` for toggle behavior
   - Implement `on_ready()`, `on_key_down()`, `update_state()`
3. Import in `main.py`
4. Create `ActionHolder` in `GoogleMeetPlugin.__init__()`
5. Add icon assets to `assets/`

### Adding a New Backend Method

1. Add method to `Backend` class in `backend/backend.py`
2. Add corresponding method to `GoogleMeetsController` if needed
3. Update actions to call new method

### Adding a New WebSocket Command

1. Add command handler in `GoogleMeetsController._handle_message()`
2. Add command method like `send_reaction()`
3. Document in README.md message protocol section

### Changing WebSocket Port

Users can change port in action config UI. Backend handles restart:

```python
def update_websocket_settings(self, host: str, port: int):
    self.controller.stop()
    self.controller = GoogleMeetsController(host=host, port=port)
    # Restore approved extensions
    self.controller.set_approved_extensions(...)
    self.controller.start()
```

## Dependencies

### Backend Requirements

From `backend/requirements.txt`:
- `loguru==0.7.2` - Logging
- `websockets==13.1` - WebSocket server
- `streamcontroller-plugin-tools>=2.0.1` - Backend base class

### System Requirements

- Python 3.10+ (for `match` statements)
- GTK 4.0, Adwaita 1 (provided by StreamController)

## Code Style

- **Docstrings**: Use for public methods, describe return values
- **Type hints**: Use where helpful (`-> bool`, `-> Optional[Dict]`)
- **Logging**: Use `log.info()`, `log.error()`, `log.debug()` from loguru
- **Threading**: Always `daemon=True`, descriptive `name=` parameter
- **Error handling**: Catch specific exceptions, log with context

## Known Limitations

1. **No Chrome extension yet**: Plugin code is complete but needs companion extension
2. **Placeholder icons**: All icons are copies of info.png
3. **No settings page**: Extension approval management not yet in UI
4. **No localization**: English only
5. **Single connection**: Only one extension can connect at a time
6. **Polling for state**: Uses `on_tick()` + state updates (hybrid approach)

## Future Enhancements

- Settings page for managing approved extensions
- Localization support (i18n)
- Meeting duration display
- More reaction types
- Extension auto-approval toggle
- Connection status indicator in plugin settings
- Logging level configuration
- Support for multiple concurrent meetings (future Google Meet feature)

## Debugging Tips

### Enable Backend Logging

In `backend/backend.py`:
```python
LOG.setLevel(logging.DEBUG)  # Change from ERROR
```

### Test WebSocket Server

```bash
# Check if server is running
netstat -an | grep 8765

# Test connection
wscat -c ws://127.0.0.1:8765
```

### Check Backend Process

Backend runs in separate process. If it crashes, check:
- `~/.local/share/StreamController/logs/`
- StreamController console output
- Backend dependencies installed in `.venv`

### Action Not Updating

Common causes:
1. Backend not connected: Check `get_connected()`
2. Not in meeting: Check `get_in_meeting()`
3. State not syncing: Check `on_tick()` being called
4. Exception in background thread: Check logs

## References

- [StreamController Docs](https://streamcontroller.github.io/docs/latest/)
- [OBS Plugin (reference implementation)](https://github.com/StreamController/OBSPlugin)
- [streamcontroller-plugin-tools](https://pypi.org/project/streamcontroller-plugin-tools/)
- WebSocket Protocol: RFC 6455

---

**Last Updated**: 2025-01-08
**Plugin Version**: 1.0.0
**For**: Google Meet StreamController Plugin
