/**
 * Background Service Worker for Google Meet StreamController Bridge
 *
 * Simplified version using StreamControllerClient
 */

import { StreamControllerClient } from './streamcontroller-client/index.js';
import { MeetingTabStateManager } from './meeting-tab-state-manager.js';

// Client instance
let client = null;
let connectionState = 'disconnected'; // disconnected, connecting, connected, error, pending_approval

// Tab state manager
let tabStateManager = null;

// Settings
let settings = {
  wsHost: '127.0.0.1',
  wsPort: 8765,
  autoConnect: true
};

/**
 * Initialize background script
 */
async function init() {
  console.log('[Google Meet Bridge Background] Initializing...');

  // Load settings
  await loadSettings();

  // Initialize tab state manager
  tabStateManager = new MeetingTabStateManager();
  await tabStateManager.init();

  // Listen for state changes and forward to StreamController
  tabStateManager.on('state-changed', (state) => {
    console.log('[Google Meet Bridge Background] State changed:', state);
    sendStateUpdate(state);
  });

  // Initialize client
  const serverUrl = `ws://${settings.wsHost}:${settings.wsPort}`;
  client = new StreamControllerClient({
    extensionId: chrome.runtime.id,
    serverUrl: serverUrl
  });

  // Setup event handlers
  setupClientEvents();

  // Listen for messages from content script
  chrome.runtime.onMessage.addListener(handleMessage);

  // Auto-connect if enabled
  if (settings.autoConnect) {
    setTimeout(() => connect(), 5000);
  }

  // Update badge
  updateBadge();
}


/**
 * Load settings from storage
 */
async function loadSettings() {
  try {
    const result = await chrome.storage.sync.get('settings');
    if (result.settings) {
      settings = { ...settings, ...result.settings };
    }
  } catch (error) {
    console.error('[Google Meet Bridge Background] Error loading settings:', error);
  }
}

/**
 * Save settings to storage
 */
async function saveSettings() {
  try {
    await chrome.storage.sync.set({ settings });
  } catch (error) {
    console.error('[Google Meet Bridge Background] Error saving settings:', error);
  }
}

/**
 * Setup client event handlers
 */
function setupClientEvents() {
  client.on('connected', () => {
    console.log('[Google Meet Bridge Background] Connected to StreamController');
    connectionState = 'connected';
    updateBadge();
  });

  client.on('disconnected', (reason) => {
    console.log('[Google Meet Bridge Background] Disconnected:', reason);
    connectionState = 'disconnected';
    updateBadge();
  });

  client.on('pairing-required', () => {
    console.log('[Google Meet Bridge Background] Pairing required - awaiting user approval');
    connectionState = 'pending_approval';
    updateBadge();
  });

  client.on('command', (cmd) => {
    console.log('[Google Meet Bridge Background] Received command:', cmd.action);
    handleCommand(cmd);
  });

  client.on('error', (error) => {
    console.error('[Google Meet Bridge Background] Client error:', error);
    connectionState = 'error';
    updateBadge();
  });
}

/**
 * Connect to StreamController
 */
async function connect() {
  if (!client) {
    console.error('[Google Meet Bridge Background] Client not initialized');
    return;
  }

  const state = client.getState();
  if (state.connected || state.pairingPending) {
    console.log('[Google Meet Bridge Background] Already connected or connecting');
    return;
  }

  connectionState = 'connecting';
  updateBadge();

  try {
    await client.connect();
  } catch (error) {
    console.error('[Google Meet Bridge Background] Connection error:', error);
    connectionState = 'error';
    updateBadge();
  }
}

/**
 * Disconnect from StreamController
 */
async function disconnect() {
  console.log('[Google Meet Bridge Background] Disconnecting...');

  if (client) {
    await client.disconnect();
  }

  connectionState = 'disconnected';
  updateBadge();
}

/**
 * Handle command from StreamController
 */
async function handleCommand(cmd) {
  // Forward command to active meeting tab
  try {
    const activeTabId = await tabStateManager.getActiveMeetingTabId();
    if (!activeTabId) {
      console.warn('[Google Meet Bridge Background] No active Google Meet tab found');
      return;
    }

    // Send to active meeting tab
    chrome.tabs.sendMessage(activeTabId, {
      type: 'command',
      action: cmd.action,
      data: cmd.data
    }).catch(err => {
      console.warn('[Google Meet Bridge Background] Error sending command to tab:', err);
    });

  } catch (error) {
    console.error('[Google Meet Bridge Background] Error forwarding command:', error);
  }
}

/**
 * Send state update to StreamController
 */
async function sendStateUpdate(state) {
  if (!client) {
    console.warn('[Google Meet Bridge Background] Client not initialized');
    return;
  }

  const clientState = client.getState();
  if (!clientState.connected || !clientState.authorized) {
    console.warn('[Google Meet Bridge Background] Cannot send state: not authorized');
    return;
  }

  console.log('[Google Meet Bridge Background] Sending state update:', state);
  try {
    await client.sendState(state);
    console.log('[Google Meet Bridge Background] State update sent');
  } catch (error) { 
    console.log('[Google Meet Bridge Background] State failed to send:', error);
  }
}

/**
 * Handle messages from content script or popup
 */
function handleMessage(message, sender, sendResponse) {

  switch (message.type) {
    case 'state_update':
      // Update state from content script
      if (!sender.tab) {
        console.error('[Google Meet Bridge Background] Received message that did not come from a tab');
        return false;
      }

      // Update tab state in manager (async, but don't wait for response)
      tabStateManager.updateTabState(sender.tab.id, message.state).catch(err => {
        console.error('[Google Meet Bridge Background] Error updating tab state:', err);
      });
      return false; // No async response needed

    case 'get_status':
      // Send status to popup (async)
      (async () => {
        try {
          const currentState = await tabStateManager.getCurrentState();
          console.log('[Google Meet Bridge Background] Sending status to popup:', {
            connectionState,
            currentState,
            settings
          });
          sendResponse({
            connectionState: connectionState,
            currentState: currentState,
            settings: settings
          });
        } catch (error) {
          console.error('[Google Meet Bridge Background] Error getting status:', error);
          sendResponse({
            connectionState: 'error',
            currentState: null,
            settings: settings
          });
        }
      })();
      return true; // Keep channel open for async response

    case 'connect':
      connect();
      sendResponse({ success: true });
      return false;

    case 'disconnect':
      disconnect();
      sendResponse({ success: true });
      return false;

    case 'update_settings':
      settings = { ...settings, ...message.settings };
      saveSettings();
      sendResponse({ success: true });
      return false;

    default:
      console.warn('[Google Meet Bridge Background] Unknown message type:', message.type);
      return false;
  }
}

/**
 * Update extension badge
 */
function updateBadge() {
  const badgeConfig = {
    disconnected: { text: '', color: '#666666' },
    connecting: { text: '...', color: '#FFA500' },
    pending_approval: { text: '?', color: '#FFA500' },
    connected: { text: '✓', color: '#00AA00' },
    error: { text: '✗', color: '#FF0000' }
  };

  const config = badgeConfig[connectionState] || badgeConfig.disconnected;

  chrome.action.setBadgeText({ text: config.text });
  chrome.action.setBadgeBackgroundColor({ color: config.color });
}

// Initialize
init();
