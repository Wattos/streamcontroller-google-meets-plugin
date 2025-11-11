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
2. run `npm run build`
3. Open Chrome and navigate to `chrome://extensions/`
4. Enable "Developer mode" (toggle in top-right corner)
5. Click "Load unpacked"
6. Select the `chrome_extension/dist` directory
7. The extension should now appear in your extensions list

### From Chrome Web Store

*Coming soon - extension not yet published*


## License

MIT License - See LICENSE file

