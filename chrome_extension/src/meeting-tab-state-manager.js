/**
 * MeetingTabStateManager
 *
 * Manages state for multiple Google Meet tabs and determines which
 * meeting state should be forwarded to StreamController.
 *
 * Provides a simple event-based API - consumers just listen for
 * 'state-changed' events and don't need to worry about tab management.
 *
 * Uses chrome.storage.local exclusively (no in-memory state) to survive
 * service worker restarts.
 */

const TAB_STATE_TIMEOUT = 60000; // 60 seconds
const CLEANUP_INTERVAL = 5000; // Clean every 5 seconds
const STORAGE_KEY = 'meetingTabState'; // Key for chrome.storage.local

// Default state when no meetings are active
const NULL_STATE = {
  mic_enabled: false,
  camera_enabled: false,
  hand_raised: false,
  in_meeting: false,
  meeting_id: null,
  meeting_name: null,
  participant_count: 0
};

export class MeetingTabStateManager {
  constructor(options = {}) {
    this.timeout = options.timeout || TAB_STATE_TIMEOUT;
    this.cleanupInterval = options.cleanupInterval || CLEANUP_INTERVAL;

    // Event listeners
    this.listeners = {
      'state-changed': []
    };

    // Start periodic cleanup
    this.cleanupTimer = setInterval(() => this._cleanStaleStates(), this.cleanupInterval);
  }

  /**
   * Initialize and restore state from storage
   * Call this after creating the manager
   * @returns {Promise<void>}
   */
  async init() {
    // Clean stale states on startup
    await this._cleanStaleStates();
  }

  /**
   * Update state for a specific tab
   * @param {number} tabId - Tab ID
   * @param {Object} state - Meeting state object
   * @returns {Promise<void>}
   */
  async updateTabState(tabId, state) {
    // Clean stale states first
    await this._cleanStaleStates();

    // Get current state before update
    const previousState = await this.getCurrentState();

    // Read current storage
    const storageData = await this._readStorage();

    // Update tab state
    storageData.tabStates[tabId] = {
      tabId: tabId,
      state: state,
      last_updated: Date.now()
    };

    // Update active meeting ID
    storageData.activeMeetingTabId = this._findActiveMeetingTabIdFromStates(storageData.tabStates);

    // Write back to storage
    await this._writeStorage(storageData);

    // Get new state after update
    const newState = await this.getCurrentState();

    // Emit state-changed if state actually changed
    if (JSON.stringify(previousState) !== JSON.stringify(newState)) {
      this._emit('state-changed', newState);
    }
  }

  /**
   * Get current state (active meeting state or NULL_STATE)
   * @returns {Promise<Object>} Current meeting state
   */
  async getCurrentState() {
    const storageData = await this._readStorage();

    if (storageData.activeMeetingTabId && storageData.tabStates[storageData.activeMeetingTabId]) {
      return storageData.tabStates[storageData.activeMeetingTabId].state;
    }

    // No active meeting - return NULL_STATE
    return { ...NULL_STATE };
  }

  /**
   * Get active meeting tab ID
   * @returns {Promise<number|null>} Active tab ID or null
   */
  async getActiveMeetingTabId() {
    const storageData = await this._readStorage();
    return storageData.activeMeetingTabId;
  }

  /**
   * Register event listener
   * @param {string} event - Event name ('state-changed')
   * @param {Function} callback - Callback function
   */
  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  /**
   * Remove event listener
   * @param {string} event - Event name
   * @param {Function} callback - Callback function
   */
  off(event, callback) {
    if (!this.listeners[event]) return;

    this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
  }

  /**
   * Cleanup and destroy manager
   */
  destroy() {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
      this.cleanupTimer = null;
    }

    this.listeners = {};
  }

  /**
   * Read storage data
   * @private
   * @returns {Promise<Object>} Storage data
   */
  async _readStorage() {
    try {
      const result = await chrome.storage.local.get(STORAGE_KEY);

      if (result[STORAGE_KEY]) {
        return result[STORAGE_KEY];
      }
    } catch (error) {
      console.error('[MeetingTabStateManager] Error reading storage:', error);
    }

    // Return default structure
    return {
      tabStates: {},
      activeMeetingTabId: null
    };
  }

  /**
   * Write storage data
   * @private
   * @param {Object} data - Data to write
   * @returns {Promise<void>}
   */
  async _writeStorage(data) {
    try {
      await chrome.storage.local.set({
        [STORAGE_KEY]: data
      });
    } catch (error) {
      console.error('[MeetingTabStateManager] Error writing storage:', error);
    }
  }

  /**
   * Clean stale tab states (internal)
   * @private
   * @returns {Promise<void>}
   */
  async _cleanStaleStates() {
    const now = Date.now();
    const storageData = await this._readStorage();
    let deleted = false;

    for (const tabId of Object.keys(storageData.tabStates)) {
      if (now - storageData.tabStates[tabId].last_updated > this.timeout) {
        delete storageData.tabStates[tabId];
        deleted = true;
      }
    }

    // If we deleted any tabs, update active meeting
    if (deleted) {
      const previousState = await this.getCurrentState();

      storageData.activeMeetingTabId = this._findActiveMeetingTabIdFromStates(storageData.tabStates);

      await this._writeStorage(storageData);

      const newState = await this.getCurrentState();

      // Emit state-changed if state changed (e.g., active meeting gone)
      if (JSON.stringify(previousState) !== JSON.stringify(newState)) {
        this._emit('state-changed', newState);
      }
    }
  }

  /**
   * Find active meeting tab ID from given tab states
   * @private
   * @param {Object} tabStates - Tab states object
   * @returns {number|null} Active tab ID or null
   */
  _findActiveMeetingTabIdFromStates(tabStates) {
    // Find first tab that is in a meeting
    for (const tabId of Object.keys(tabStates)) {
      if (tabStates[tabId].state.in_meeting) {
        return parseInt(tabId, 10);
      }
    }
    return null;
    }

  /**
   * Emit event (internal)
   * @private
   * @param {string} event - Event name
   * @param {*} data - Event data
   */
  _emit(event, data) {
    if (!this.listeners[event]) return;

    for (const callback of this.listeners[event]) {
      try {
        callback(data);
      } catch (error) {
        console.error(`[MeetingTabStateManager] Error in ${event} listener:`, error);
      }
    }
  }
}
