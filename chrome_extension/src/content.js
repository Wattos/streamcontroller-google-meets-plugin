/**
 * Content Script for Google Meet StreamController Bridge
 *
 * Orchestrates Google Meet state detection and command execution
 * using modular feature components
 */

import { getMicrophoneState, toggleMicrophone } from './google-meet/microphone.js';
import { getCameraState, toggleCamera } from './google-meet/camera.js';
import { getHandState, toggleHand } from './google-meet/hand-raising.js';
import { sendReaction } from './google-meet/reactions.js';
import {
  waitForMeeting,
  isInMeeting,
  getMeetingId,
  getMeetingName,
  getParticipantCount,
  leaveCall
} from './google-meet/meeting-info.js';
import { observer } from './google-meet/core/observer.js';

// Current meeting state
let currentState = {
  mic_enabled: false,
  camera_enabled: false,
  hand_raised: false,
  in_meeting: false,
  meeting_id: null,
  meeting_name: null,
  participant_count: 0
};

/**
 * Initialize content script
 */
function init() {
  console.log('[Google Meet Bridge] Content script initialized');

  // Wait for meeting to load
  detectMeeting();

  // Listen for commands from background script
  chrome.runtime.onMessage.addListener(handleCommand);
  
  setInterval(() => detectMeeting(true), 5000);

  // Periodically update state in case of missed events
  setInterval(() => updateState(), 5000);

  // Longer interval full state refresh
  setInterval(() => updateState(true), 25000);

  // Start observing state changes
  observer.startObserving(() => updateState());
}

/**
 * Detect if we're in a meeting
 */
async function detectMeeting() {
  console.log('[Google Meet Bridge] Detecting meeting...'); 
  const inMeeting = await waitForMeeting(5000);
  console.log('[Google Meet Bridge] Meeting detection result:', inMeeting); 

  if (inMeeting && currentState.in_meeting === inMeeting) {
    return;
  }

  if (inMeeting) {
    currentState.in_meeting = true;
    currentState.meeting_id = getMeetingId();

    console.log('[Google Meet Bridge] Meeting detected:', currentState.meeting_id);

    // Send initial state
    setTimeout(() => updateState(), 1000);
    sendStateUpdate();
  } else {
    currentState.in_meeting = false;
    currentState.meeting_id = null;
  }
}

/**
 * Update current state by checking all feature modules
 */
function updateState(force) {
  if (!currentState.in_meeting) {
    return;
  }

  const newState = {
    mic_enabled: getMicrophoneState(),
    camera_enabled: getCameraState(),
    hand_raised: getHandState(),
    in_meeting: isInMeeting(),
    meeting_id: getMeetingId(),
    meeting_name: getMeetingName(),
    participant_count: getParticipantCount()
  };

  // Check if state changed
  if (force || (JSON.stringify(newState) !== JSON.stringify(currentState))) {
    currentState = newState;
    console.log('[Google Meet Bridge] State changed:', currentState);
    sendStateUpdate();
  }
}

/**
 * Send state update to background script
 */
function sendStateUpdate() {
  chrome.runtime.sendMessage({
    type: 'state_update',
    state: currentState
  }).catch(err => {
    console.error('[Google Meet Bridge] Error sending state:', err);
  });
}

/**
 * Handle commands from background script (via StreamController)
 */
async function handleCommand(message, sender, sendResponse) {
  if (message.type !== 'command') {
    return;
  }

  console.log('[Google Meet Bridge] Received command:', message.action);

  try {
    switch (message.action) {
      case 'toggle_mic':
        await toggleMicrophone();
        break;

      case 'toggle_camera':
        await toggleCamera();
        break;

      case 'toggle_hand':
        await toggleHand();
        break;

      case 'send_reaction':
        await sendReaction(message.data?.reaction);
        break;

      case 'leave_call':
        await leaveCall();
        break;

      case 'get_state':
        updateState(true);
        break;

      default:
        console.warn('[Google Meet Bridge] Unknown command:', message.action);
    }

    // Update state after command
    setTimeout(() => updateState(), 100);

    sendResponse({ success: true });
  } catch (error) {
    console.error('[Google Meet Bridge] Error executing command:', error);
    sendResponse({ success: false, error: error.message });
  }

  return true; // Keep message channel open for async response
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
