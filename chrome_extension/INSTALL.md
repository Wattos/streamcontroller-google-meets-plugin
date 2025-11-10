# Installation Guide - Google Meet StreamController Bridge Extension

Step-by-step guide to install and configure the Chrome extension.

## Prerequisites

1. **Google Chrome** (or Chromium-based browser like Edge, Brave)
2. **StreamController** installed and running
3. **Google Meet Plugin** for StreamController installed
4. **Google Meet** account

## Step 1: Load the Extension

### Option A: Developer Mode (Recommended for Testing)

1. Open Google Chrome
2. Navigate to `chrome://extensions/`
3. **Enable Developer Mode**:
   - Look for toggle switch in top-right corner
   - Click to enable
4. Click **"Load unpacked"** button
5. Navigate to the extension directory:
   ```
   [plugin_directory]/chrome_extension/
   ```
6. Click **"Select Folder"**
7. Extension should appear in your extensions list

### Option B: From Chrome Web Store

*Coming soon - not yet published*

## Step 2: Verify Extension Installation

1. Look for extension icon in Chrome toolbar (top-right)
   - If not visible, click puzzle icon (🧩) to see all extensions
   - Pin the extension for easy access
2. Click extension icon
3. Popup should open showing:
   - Connection status: "Disconnected"
   - Settings section with default values

## Step 3: Configure StreamController

1. **Launch StreamController**
2. **Install Google Meet Plugin**:
   - If not already installed
   - Navigate to plugin store or install from directory
3. **Verify Plugin is Running**:
   - The plugin starts a WebSocket server on port 8765
   - Check plugin settings or logs to confirm
4. **Note**: First connection will require approval (next step)

## Step 4: Connect Extension to StreamController

1. **Open Extension Popup**:
   - Click extension icon in Chrome toolbar
2. **Verify Settings**:
   - WebSocket Host: `127.0.0.1`
   - WebSocket Port: `8765`
   - Auto-connect: ✓ (checked)
3. **Click "Connect to StreamController"**
4. **Connection States**:
   - "Connecting..." - Attempting connection
   - "Awaiting Approval" - Waiting for user approval in StreamController
   - "Connected" ✓ - Successfully connected

## Step 5: Approve Extension (First Time Only)

1. **In StreamController**:
   - A notification or dialog should appear
   - Message: "Chrome extension requesting connection"
   - Extension ID will be shown
2. **Approve the Connection**:
   - Click "Approve" or "Accept"
   - This approval is saved for future connections
3. **In Chrome Extension**:
   - Status should change to "Connected" ✓
   - Green indicator appears

## Step 6: Test the Connection

### Test 1: Join a Meeting

1. Navigate to [meet.google.com](https://meet.google.com)
2. Join or create a meeting
3. **Check Extension Popup**:
   - Should show "In meeting: [meeting-code]"
   - Current State section should appear
   - Mic/Camera/Hand states should display

### Test 2: Test State Detection

1. In Google Meet, click microphone button to mute
2. Check extension popup:
   - Mic state should update to "OFF"
3. Unmute microphone
4. Check extension popup:
   - Mic state should update to "ON"
5. Repeat for camera and hand

### Test 3: Test StreamController Control

1. **Add Action to Stream Deck**:
   - In StreamController, drag "Toggle Microphone" action to a button
2. **Press the Button**:
   - Microphone should toggle in Google Meet
   - Button icon should update to show new state
3. **Repeat for other actions**:
   - Toggle Camera
   - Raise Hand
   - Send Reaction

## Troubleshooting

### Extension Not Appearing in Chrome

- **Solution**: Ensure you selected the correct directory (`chrome_extension/`)
- **Check**: Look for `manifest.json` in the selected folder
- **Try**: Reload the extension (chrome://extensions → Click reload icon)

### Connection Status: "Connection Error"

**Possible Causes**:
1. StreamController not running
2. Wrong WebSocket port
3. Firewall blocking connection

**Solutions**:
1. Verify StreamController is running
2. Check plugin settings for WebSocket port
3. Update extension settings to match
4. Click "Disconnect" then "Connect" again

### Status Stuck on "Connecting..."

**Possible Causes**:
1. StreamController plugin not started
2. Network issue
3. Port already in use

**Solutions**:
1. Restart StreamController
2. Check console for errors:
   - chrome://extensions → Click "Service Worker"
   - Look for WebSocket errors
3. Try different port (e.g., 8766)

### Status Stuck on "Awaiting Approval"

**Possible Causes**:
1. Approval dialog not appearing in StreamController
2. Approval timed out

**Solutions**:
1. Check StreamController for approval dialog
2. Check plugin settings for "pending approvals"
3. Click "Disconnect" and try again
4. Restart both StreamController and Chrome

### Extension Connected but No Meeting Detected

**Possible Causes**:
1. Not in a Google Meet meeting yet
2. Meeting still loading
3. DOM selectors not matching

**Solutions**:
1. Wait a few seconds after joining meeting
2. Refresh the Google Meet page
3. Check browser console (F12) for errors
4. Verify you're on `meet.google.com` (not `hangouts.google.com`)

### Controls Not Working (Can't Toggle Mic/Camera)

**Possible Causes**:
1. Google Meet UI changed
2. Permissions not granted to Meet
3. Meeting controls locked

**Solutions**:
1. Try manually clicking buttons in Meet
2. Check if mic/camera permissions granted
3. Check browser console for errors
4. Update extension if available

### State Not Updating in StreamController

**Possible Causes**:
1. WebSocket connection dropped
2. State update messages not being sent
3. StreamController not receiving updates

**Solutions**:
1. Check extension popup shows "Connected"
2. Check background service worker console:
   - chrome://extensions → "Service Worker"
   - Look for "State update sent" messages
3. Restart both extension and StreamController

## Advanced Configuration

### Custom WebSocket Port

If you changed the WebSocket port in StreamController:

1. Open extension popup
2. Update "WebSocket Port" field
3. Click "Save Settings"
4. Disconnect and reconnect

### Disable Auto-Connect

If you don't want automatic connection:

1. Open extension popup
2. Uncheck "Auto-connect on startup"
3. Click "Save Settings"
4. Manually click "Connect" when needed

### Checking Logs

**Extension Console**:
```
1. chrome://extensions/
2. Enable Developer Mode
3. Click "Service Worker" under extension
4. View console logs
```

**Content Script Console**:
```
1. Open Google Meet
2. Press F12
3. Go to Console tab
4. Filter for "Google Meet Bridge"
```

### Debugging WebSocket

**Check Connection**:
```bash
# On Linux/Mac
netstat -an | grep 8765

# Should show LISTENING
```

**Test WebSocket Server**:
```bash
# Install wscat
npm install -g wscat

# Connect to server
wscat -c ws://127.0.0.1:8765

# Should connect successfully
```

## Uninstallation

### Remove Extension

1. Go to `chrome://extensions/`
2. Find "Google Meet StreamController Bridge"
3. Click "Remove"
4. Confirm removal

### Clean Up Data

Extension data stored in Chrome sync storage will be automatically cleaned up. To manually clear:

1. chrome://settings/clearBrowserData
2. Select "Cookies and other site data"
3. Select time range
4. Click "Clear data"

## Getting Help

If you continue to have issues:

1. **Check Console Logs**:
   - Background service worker console
   - Content script console (F12 on Meet page)
   - StreamController logs

2. **Verify Setup**:
   - StreamController running?
   - Plugin installed?
   - WebSocket port correct?
   - Extension connected?

3. **Report Issue**:
   - GitHub Issues: [Link to repo]
   - Include console logs
   - Include extension version
   - Include steps to reproduce

## Next Steps

After successful installation:

1. **Configure Stream Deck Actions**:
   - Add Toggle Microphone
   - Add Toggle Camera
   - Add Raise Hand
   - Add Send Reaction (configure reaction type)

2. **Customize Icons**:
   - Replace placeholder icons in `assets/` directory
   - See `assets/ASSETS_NEEDED.md` for requirements

3. **Join Meetings**:
   - Extension will auto-detect meetings
   - States will sync automatically
   - Use Stream Deck to control meeting

Enjoy controlling Google Meet from your Stream Deck! 🎉
