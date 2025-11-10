# Google Meet Controller Plugin for StreamController

Control Google Meet from your Stream Deck with real-time state synchronization!

## Features

- **Toggle Microphone** - Mute/unmute with visual feedback
- **Toggle Camera** - Turn camera on/off with state display
- **Raise/Lower Hand** - Raise your hand in meetings
- **Send Reactions** - Send emoji reactions (💖 👍 🎉 👏 😂 😮 😢 🤔 👎)
- **Real-time Sync** - Button states update automatically based on actual meeting state
- **Secure Communication** - JWS ES256 authenticated WebSocket with instance-based approval

## Architecture

This plugin follows a clean separation of concerns:

### Backend (`backend/`)
- **auth/**: Authentication and pairing management
  - **CryptoManager**: JWS signing/verification with ES256 keys
  - **PairingManager**: Instance-based pairing approval and storage with rich metadata

- **GoogleMeetsController**: WebSocket server that communicates with Chrome extension
  - Runs on `127.0.0.1:8765` (configurable)
  - Handles handshake and JWS ES256 authentication
  - Manages instance approval and public key storage
  - Provides real-time state updates

- **Backend**: Wrapper that exposes clean API to StreamController actions
  - `toggle_microphone()`, `toggle_camera()`, `toggle_hand()`
  - `send_reaction(reaction)`
  - `get_state()` - returns current mic/camera/hand state
  - `approve_instance()`, `deny_instance()`, `revoke_instance()`

### Actions (`actions/`)
- **ToggleMic**: Toggle microphone with ON/OFF state display
- **ToggleCamera**: Toggle camera with ON/OFF state display
- **RaiseHand**: Raise/lower hand with RAISED state display
- **SendReaction**: Send reactions with configurable reaction selection

All actions extend `GoogleMeetActionBase` and use the mixin pattern for reusable behavior.

## Installation

1. Clone this plugin into your StreamController plugins directory:
   ```bash
   cd ~/.local/share/StreamController/plugins/
   git clone https://github.com/Wattos/streamcontroller-google-meets-plugin.git
   ```

2. Install the Chrome extension (see `chrome-extension/` directory)

3. Restart StreamController

## Chrome Extension

The Chrome extension provides secure communication between Google Meet and StreamController:

### Features
- **Modular Architecture**: Feature-based organization (microphone, camera, hand-raising, reactions, meeting-info)
- **StreamControllerClient**: Clean abstraction for WebSocket communication
- **ES256 Key Pair**: Generated in browser using Web Crypto API
- **Instance-Based Pairing**: Each browser instance (profile) gets unique identity
- **Rich Metadata**: Pairing requests include browser name, version, OS info

### Pairing Flow

1. Extension generates ES256 key pair on first run
2. Connects to WebSocket server at `ws://127.0.0.1:8765`
3. Sends handshake with extension ID, instance ID, public key, and metadata
4. User approves instance in StreamController (sees browser, OS, user info)
5. All subsequent messages signed with JWS using private key
6. Server verifies signatures using stored public key

### Message Protocol

#### Handshake (Pairing)
```json
{
  "type": "handshake",
  "extension_id": "chrome_extension_id",
  "instance_id": "uuid-v4",
  "public_key": {
    "kty": "EC",
    "crv": "P-256",
    "x": "...",
    "y": "..."
  },
  "metadata": {
    "extension_name": "Google Meet StreamController Bridge",
    "extension_version": "1.0.0",
    "browser_name": "Chrome",
    "browser_version": "120.0",
    "os": "Linux",
    "timestamp": 1234567890
  }
}
```

Server responds after approval:
```json
{
  "type": "handshake_success",
  "message": "Pairing approved"
}
```

#### Authenticated Messages
All non-handshake messages include JWS token:
```json
{
  "type": "state|heartbeat",
  "extension_id": "...",
  "instance_id": "...",
  "data": {
    "mic_enabled": true,
    "camera_enabled": false,
    "hand_raised": false,
    "in_meeting": true,
    "meeting_name": "Team Standup",
    "participant_count": 5
  },
  "token": "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

The token payload contains:
```json
{
  "type": "state",
  "instance_id": "...",
  "data": { ... },
  "iat": 1234567890,
  "exp": 1234568190
}
```

## Security

- **Localhost only**: WebSocket server binds to 127.0.0.1
- **Instance approval**: Each browser instance must be approved in plugin settings
- **JWS ES256 authentication**: All messages signed with asymmetric cryptography
  - Extension generates ES256 key pair in browser
  - Public key shared during pairing
  - Private key never leaves browser
  - Messages signed with JWS compact serialization
  - Server verifies using stored public key
- **Instance isolation**: Each browser instance (profile) has unique identity
- **Rich metadata**: Pairing requests include browser, OS, and user info for context

## Configuration

Actions can be configured with:
- WebSocket port (default: 8765)
- Reaction selection (for SendReaction action)

## Development

### Project Structure
```
.
├── actions/
│   ├── mixins/              # Reusable action behaviors
│   ├── GoogleMeetActionBase.py  # Base class for all actions
│   ├── ToggleMic.py
│   ├── ToggleCamera.py
│   ├── RaiseHand.py
│   └── SendReaction.py
├── backend/
│   ├── auth/                # Authentication modules
│   │   ├── crypto_manager.py   # JWS ES256 crypto operations
│   │   ├── pairing_manager.py  # Instance pairing management
│   │   └── __init__.py
│   ├── GoogleMeetsController.py  # WebSocket server
│   ├── backend.py                # Backend wrapper
│   └── requirements.txt
├── chrome_extension/
│   ├── src/
│   │   ├── streamcontroller-client/  # Reusable client abstraction
│   │   │   ├── index.js             # Main StreamControllerClient
│   │   │   ├── websocket-manager.js
│   │   │   ├── pairing-manager.js
│   │   │   ├── auth-manager.js      # ES256 key & JWS signing
│   │   │   └── metadata-collector.js
│   │   ├── google-meet/             # Feature modules
│   │   │   ├── core/               # Shared utilities
│   │   │   │   ├── dom-utils.js
│   │   │   │   ├── button-controller.js
│   │   │   │   └── observer.js
│   │   │   ├── microphone.js
│   │   │   ├── camera.js
│   │   │   ├── hand-raising.js
│   │   │   ├── reactions.js
│   │   │   └── meeting-info.js
│   │   ├── background.js           # Service worker
│   │   └── content.js              # Main coordinator
│   ├── manifest.json
│   └── README.md
├── assets/               # Icons
├── main.py              # Plugin registration
├── manifest.json        # Plugin metadata
└── README.md

```

### Icons

Currently using placeholder icons. See `assets/ASSETS_NEEDED.md` for details on required icons.

### Testing

1. **Without extension**: Plugin will show "No Connection" status
2. **With extension**:
   - Install extension in Chrome
   - Join a Google Meet
   - Extension will request pairing
   - Approve in StreamController settings
   - Test mic/camera/hand/reaction controls

3. **With mock extension**: Create a test WebSocket client that:
   - Generates ES256 key pair
   - Connects to ws://127.0.0.1:8765
   - Sends handshake with public key and metadata
   - Signs all messages with JWS
   - Responds to commands
   - Sends state updates

## TODO

- [x] Implement Chrome extension with modular architecture
- [x] Implement JWS ES256 authentication
- [x] Implement instance-based pairing
- [ ] Create proper icon assets
- [ ] Add localization support
- [ ] Add comprehensive testing suite
- [ ] Add logging/debugging options

## License

MIT License - See LICENSE file

## Credits

Built following StreamController plugin architecture patterns from the [OBS Plugin](https://github.com/StreamController/OBSPlugin).
