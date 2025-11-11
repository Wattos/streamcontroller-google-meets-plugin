/**
 * Popup UI Script for Google Meet StreamController Bridge
 */

// DOM elements
let connectionIndicator;
let connectionStatus;
let meetingStatus;
let meetingStateSection;
let micState;
let cameraState;
let handState;
let connectButton;
let disconnectButton;
let wsHostInput;
let wsPortInput;
let autoConnectCheckbox;
let saveSettingsButton;

// Current status
let currentStatus = null;

/**
 * Initialize popup
 */
document.addEventListener('DOMContentLoaded', async () => {
  // Get DOM elements
  connectionIndicator = document.getElementById('connection-indicator');
  connectionStatus = document.getElementById('connection-status');
  meetingStatus = document.getElementById('meeting-status');
  meetingStateSection = document.getElementById('meeting-state-section');
  micState = document.getElementById('mic-state');
  cameraState = document.getElementById('camera-state');
  handState = document.getElementById('hand-state');
  connectButton = document.getElementById('connect-button');
  disconnectButton = document.getElementById('disconnect-button');
  wsHostInput = document.getElementById('ws-host');
  wsPortInput = document.getElementById('ws-port');
  autoConnectCheckbox = document.getElementById('auto-connect');
  saveSettingsButton = document.getElementById('save-settings');

  // Set up event listeners
  connectButton.addEventListener('click', handleConnect);
  disconnectButton.addEventListener('click', handleDisconnect);
  saveSettingsButton.addEventListener('click', handleSaveSettings);

  // Load current status
  await loadStatus();

  // Update UI periodically
  setInterval(loadStatus, 2000);
});

/**
 * Load current status from background script
 */
async function loadStatus() {
  try {
    console.log('[Popup] Requesting status from background...');
    const response = await chrome.runtime.sendMessage({ type: 'get_status' });
    console.log('[Popup] Received status:', response);

    if (!response) {
      console.error('[Popup] No response from background script');
      return;
    }

    currentStatus = response;
    updateUI();
  } catch (error) {
    console.error('[Popup] Error loading status:', error);
    // Show error state in UI
    connectionStatus.textContent = 'Error loading status';
    connectionIndicator.classList.add('error');
  }
}

/**
 * Update UI based on current status
 */
function updateUI() {
  if (!currentStatus) {
    console.log('[Popup] No current status - skipping UI update');
    return;
  }

  console.log('[Popup] Updating UI with status:', currentStatus);

  // Update connection status
  updateConnectionStatus(currentStatus.connectionState);

  // Update meeting status
  updateMeetingStatus(currentStatus.currentState);

  // Update settings inputs
  if (currentStatus.settings) {
    wsHostInput.value = currentStatus.settings.wsHost || '127.0.0.1';
    wsPortInput.value = currentStatus.settings.wsPort || 8765;
    autoConnectCheckbox.checked = currentStatus.settings.autoConnect !== false;
  }
}

/**
 * Update connection status display
 */
function updateConnectionStatus(state) {
  // Remove all state classes
  connectionIndicator.classList.remove('connected', 'connecting', 'disconnected', 'error');

  // Map states to display
  const statusMap = {
    disconnected: {
      class: 'disconnected',
      text: 'Disconnected',
      showConnect: true,
      showDisconnect: false
    },
    connecting: {
      class: 'connecting',
      text: 'Connecting...',
      showConnect: false,
      showDisconnect: true
    },
    pending_approval: {
      class: 'connecting',
      text: 'Awaiting Approval',
      showConnect: false,
      showDisconnect: true
    },
    connected: {
      class: 'connected',
      text: 'Connected',
      showConnect: false,
      showDisconnect: true
    },
    error: {
      class: 'error',
      text: 'Connection Error',
      showConnect: true,
      showDisconnect: false
    }
  };

  const status = statusMap[state] || statusMap.disconnected;

  connectionIndicator.classList.add(status.class);
  connectionStatus.textContent = status.text;

  // Show/hide buttons
  connectButton.style.display = status.showConnect ? 'block' : 'none';
  disconnectButton.style.display = status.showDisconnect ? 'block' : 'none';
}

/**
 * Update meeting status display
 */
function updateMeetingStatus(state) {
  console.log('[Popup] Updating meeting status with state:', state);

  if (!state) {
    console.log('[Popup] No state available - showing not in meeting');
    meetingStatus.textContent = 'Not in meeting';
    meetingStateSection.style.display = 'none';
    return;
  }

  if (state.in_meeting) {
    const meetingId = state.meeting_id || 'Unknown';
    const meetingName = state.meeting_name || meetingId;
    const participantCount = state.participant_count || 0;

    console.log('[Popup] In meeting:', { meetingId, meetingName, participantCount });

    meetingStatus.textContent = participantCount > 0
      ? `In meeting (${participantCount} participants)`
      : `In meeting: ${meetingName}`;
    meetingStateSection.style.display = 'block';

    // Update state indicators
    updateStateIndicator(micState, state.mic_enabled, 'ON', 'OFF');
    updateStateIndicator(cameraState, state.camera_enabled, 'ON', 'OFF');
    updateStateIndicator(handState, state.hand_raised, 'Raised', 'Lowered');
  } else {
    console.log('[Popup] Not in meeting (in_meeting =', state.in_meeting, ')');
    meetingStatus.textContent = 'Not in meeting';
    meetingStateSection.style.display = 'none';
  }
}

/**
 * Update individual state indicator
 */
function updateStateIndicator(element, isEnabled, enabledText, disabledText) {
  element.classList.remove('state-enabled', 'state-disabled');
  element.classList.add(isEnabled ? 'state-enabled' : 'state-disabled');
  element.textContent = isEnabled ? enabledText : disabledText;
}

/**
 * Handle connect button click
 */
async function handleConnect() {
  try {
    connectButton.disabled = true;
    connectButton.textContent = 'Connecting...';

    await chrome.runtime.sendMessage({ type: 'connect' });

    // Wait a bit then reload status
    setTimeout(loadStatus, 500);
  } catch (error) {
    console.error('[Popup] Error connecting:', error);
    alert('Failed to connect. Make sure StreamController is running.');
  } finally {
    connectButton.disabled = false;
    connectButton.textContent = 'Connect to StreamController';
  }
}

/**
 * Handle disconnect button click
 */
async function handleDisconnect() {
  try {
    disconnectButton.disabled = true;

    await chrome.runtime.sendMessage({ type: 'disconnect' });

    // Wait a bit then reload status
    setTimeout(loadStatus, 500);
  } catch (error) {
    console.error('[Popup] Error disconnecting:', error);
  } finally {
    disconnectButton.disabled = false;
  }
}

/**
 * Handle save settings button click
 */
async function handleSaveSettings() {
  try {
    saveSettingsButton.disabled = true;
    saveSettingsButton.textContent = 'Saving...';

    const settings = {
      wsHost: wsHostInput.value.trim(),
      wsPort: parseInt(wsPortInput.value),
      autoConnect: autoConnectCheckbox.checked
    };

    // Validate
    if (!settings.wsHost) {
      alert('WebSocket host cannot be empty');
      return;
    }

    if (settings.wsPort < 1 || settings.wsPort > 65535) {
      alert('WebSocket port must be between 1 and 65535');
      return;
    }

    // Save settings
    await chrome.runtime.sendMessage({
      type: 'update_settings',
      settings: settings
    });

    saveSettingsButton.textContent = 'Saved!';
    setTimeout(() => {
      saveSettingsButton.textContent = 'Save Settings';
    }, 2000);

    // Show reconnect message if connected
    if (currentStatus && currentStatus.connectionState === 'connected') {
      alert('Settings saved. Please disconnect and reconnect for changes to take effect.');
    }
  } catch (error) {
    console.error('[Popup] Error saving settings:', error);
    alert('Failed to save settings');
  } finally {
    saveSettingsButton.disabled = false;
  }
}
