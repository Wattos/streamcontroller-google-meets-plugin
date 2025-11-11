# Google Meet StreamController Bridge - Chrome Extension

Chrome extension that connects Google Meet to StreamController, enabling control of microphone, camera, hand raising, and reactions from a Stream Deck.

## Features

- 🎤 **Microphone Control** - Toggle mute/unmute
- 📹 **Camera Control** - Toggle camera on/off
- ✋ **Hand Raising** - Raise and lower hand
- 😊 **Reactions** - Send emoji reactions (👍 ❤️ 😂 😮 👏 🎉)
- 🔄 **Real-time Sync** - Automatic state updates to StreamController
- 🔒 **Secure** - HMAC-authenticated WebSocket connection
- ⚡ **Auto-reconnect** - Automatic reconnection on disconnect

## Installation

### From Source (Developer Mode)

1. Clone or download this repository
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable "Developer mode" (toggle in top-right corner)
4. Click "Load unpacked"
5. Select the `chrome_extension` directory
6. The extension should now appear in your extensions list

### From Chrome Web Store

*Coming soon - extension not yet published*

## Setup

1. **Install StreamController Plugin**
   - Install the Google Meet plugin for StreamController
   - The plugin will start a WebSocket server on `127.0.0.1:8765`

2. **Configure Extension**
   - Click the extension icon in Chrome toolbar
   - Verify settings (default: `127.0.0.1:8765`)

3. **Approve Connection** (First Time)
   - Extension will request approval in StreamController
   - Approve the connection in StreamController settings
   - Extension will connect and show "Connected" status

4. **Join a Google Meet**
   - Navigate to any Google Meet meeting
   - The extension will automatically detect the meeting
   - State updates will be sent to StreamController

## Usage

### Extension Popup

Click the extension icon to see:
- **Connection Status** - Shows if connected to StreamController
- **Meeting Status** - Shows current meeting and ID
- **Current State** - Real-time display of mic/camera/hand state
- **Controls** - Connect/disconnect buttons
- **Settings** - WebSocket host/port configuration

### StreamController Actions

Use the following actions from StreamController:
- **Toggle Microphone** - Press to mute/unmute
- **Toggle Camera** - Press to turn camera on/off
- **Raise Hand** - Press to raise/lower hand
- **Send Reaction** - Press to send configured reaction

## Architecture

```
┌─────────────────┐
│  Google Meet    │
│     Page        │
└────────┬────────┘
         │
         │ DOM Interaction
         │
┌────────▼────────┐
│  Content Script │ ◄─── Detects state changes
│   (content.js)  │      Executes commands
└────────┬────────┘
         │
         │ chrome.runtime messages
         │
┌────────▼────────────┐
│  Background Worker  │
│   (background.js)   │ ◄─── Manages WebSocket
└────────┬────────────┘      HMAC authentication
         │                   Heartbeat
         │
         │ WebSocket (ws://127.0.0.1:8765)
         │
┌────────▼────────────┐
│  StreamController   │
│   Backend Server    │
└─────────────────────┘
```

## WebSocket Protocol

### Handshake

1. **Extension → Server**
   ```json
   {
     "type": "handshake",
     "extension_id": "chrome_extension_id"
   }
   ```

2. **Server → Extension** (Pending Approval)
   ```json
   {
     "type": "handshake_pending",
     "message": "Awaiting user approval"
   }
   ```

3. **Server → Extension** (Success)
   ```json
   {
     "type": "handshake_success",
     "session_key": "ephemeral_session_key"
   }
   ```

### State Updates

**Extension → Server**
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
  "hmac": "signature"
}
```

### Commands

**Server → Extension**
```json
{
  "type": "command",
  "action": "toggle_mic|toggle_camera|toggle_hand|send_reaction",
  "data": {
    "reaction": "thumbs_up"
  },
  "hmac": "signature"
}
```

### Heartbeat

**Extension → Server** (every 5 seconds)
```json
{
  "type": "heartbeat",
  "hmac": "signature"
}
```

**Server → Extension**
```json
{
  "type": "heartbeat_ack",
  "hmac": "signature"
}
```

## Security

- **Localhost Only** - WebSocket connects to `127.0.0.1` only
- **HMAC Authentication** - All messages signed with SHA-256 HMAC
- **User Approval** - Extensions must be approved in StreamController
- **Ephemeral Keys** - Session keys are unique per connection
- **No External Access** - Extension only runs on `meet.google.com`

## Google Meet DOM Selectors

The extension uses the following strategies to find controls:

### Microphone Button
- Searches for buttons with aria-label containing "microphone", "mic", or "mute"
- Detects state from button label (e.g., "Turn off microphone" = ON)

### Camera Button
- Searches for buttons with aria-label containing "camera"
- Detects state from button label (e.g., "Turn off camera" = ON)

### Hand Button
- Searches for buttons with aria-label containing "hand"
- Detects state from button label ("Lower hand" = RAISED)

### Reactions
- Finds reactions button by aria-label
- Opens menu and clicks specific emoji

**Note**: Google may change their UI structure. If controls stop working, the selectors may need updating.

## Troubleshooting

### Extension Not Connecting

1. Verify StreamController is running
2. Check WebSocket port (default: 8765)
3. Ensure no firewall blocking localhost connections
4. Check browser console for errors (F12 → Console)

### Commands Not Working

1. Verify you're in a Google Meet meeting
2. Check meeting controls are visible
3. Look for errors in console
4. Try manually clicking buttons to verify Meet is working

### State Not Updating

1. Check connection status in popup
2. Verify meeting is detected (check popup)
3. Look for errors in background service worker console:
   - Navigate to `chrome://extensions/`
   - Click "Service Worker" link under the extension
   - Check console for errors

### Approval Issues

1. Extension shows "Awaiting Approval" - check StreamController plugin settings
2. Check approved extensions list in plugin
3. Try revoking and re-approving extension

## Development

### File Structure

```
chrome_extension/
├── manifest.json          # Extension manifest (v3)
├── src/
│   ├── background.js      # Service worker (WebSocket manager)
│   ├── content.js         # Content script (Google Meet DOM)
│   └── utils.js           # Utility functions (HMAC, etc.)
├── popup/
│   ├── popup.html         # Extension popup UI
│   └── popup.js           # Popup logic
├── icons/
│   ├── icon16.png         # Extension icon 16x16
│   ├── icon48.png         # Extension icon 48x48
│   └── icon128.png        # Extension icon 128x128
└── README.md
```

### Testing

1. **Load extension in developer mode**
2. **Check background service worker console**:
   - `chrome://extensions/` → Click "Service Worker"
   - Monitor WebSocket connection logs
3. **Check content script console**:
   - Open Google Meet → F12 → Console
   - Monitor state detection and command execution
4. **Test with mock server**:
   - Use Python websockets to create test server
   - Verify handshake and HMAC authentication

### Debugging Commands

In content script console (Google Meet page):
```javascript
// Find microphone button
document.querySelector('[aria-label*="microphone" i]')

// Find camera button
document.querySelector('[aria-label*="camera" i]')

// Trigger command manually
chrome.runtime.sendMessage({
  type: 'command',
  action: 'toggle_mic',
  data: {}
})
```

## Known Issues

1. **Google Meet UI Changes** - Selectors may break if Google updates their UI
2. **Multiple Meetings** - Only one active meeting supported
3. **Reactions Menu** - May not work if Google changes menu structure
4. **Meeting Detection** - Can take 1-2 seconds after joining

## Future Enhancements

- [ ] Support for multiple simultaneous meetings
- [ ] Background blur/effects control
- [ ] Captions toggle
- [ ] Screen sharing control
- [ ] Participant list access
- [ ] Meeting recording control
- [ ] Layout switching
- [ ] Pin/spotlight participant

## License

MIT License - See LICENSE file

## Contributing

Contributions welcome! Areas needing help:

1. **Selector Updates** - Keep DOM selectors working as Google updates Meet
2. **Testing** - Test on different Chrome versions and operating systems
3. **Documentation** - Improve setup and troubleshooting guides
4. **Features** - Implement additional controls (see Future Enhancements)

## Support

For issues and questions:
- GitHub Issues: [Link to repo issues]
- StreamController Discord: [Link if available]

## Changelog

### Version 1.0.0 (2025-01-08)
- Initial release
- Basic mic/camera/hand controls
- Reaction support (6 emojis)
- WebSocket connection with HMAC auth
- Auto-reconnect functionality
- Popup UI for status and settings
