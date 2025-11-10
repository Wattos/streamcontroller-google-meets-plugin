/**
 * StreamController Client
 *
 * Main client class that provides a simple API for communicating with StreamController.
 * Handles authentication, pairing, signing, and message passing automatically.
 *
 * @example
 * const client = new StreamControllerClient({
 *   extensionId: chrome.runtime.id,
 *   serverUrl: 'ws://127.0.0.1:8765'
 * });
 *
 * client.on('connected', () => console.log('Connected!'));
 * client.on('command', (cmd) => handleCommand(cmd));
 *
 * await client.connect();
 * await client.sendState({ mic_enabled: true, ... });
 */

import { AuthManager } from './auth-manager.js';
import { PairingManager } from './pairing-manager.js';
import { WebSocketManager } from './websocket-manager.js';

export class StreamControllerClient {
  constructor({ extensionId, serverUrl }) {
    this.extensionId = extensionId;
    this.serverUrl = serverUrl;

    // Internal managers
    this.auth = new AuthManager();
    this.pairing = new PairingManager(extensionId, this.auth);
    this.ws = new WebSocketManager(serverUrl);

    // Event handlers
    this.eventHandlers = {};

    // Heartbeat timer
    this.heartbeatTimer = null;
    this.heartbeatInterval = 5000;  // 5 seconds

    // Setup internal event forwarding
    this._setupEventHandlers();
  }

  /**
   * Connect to StreamController server
   * Automatically handles authentication and pairing
   * @returns {Promise<void>}
   */
  async connect() {
    console.log('[StreamControllerClient] Connecting...');

    // Initialize auth (load or generate keys)
    await this.auth.initialize();

    // Connect WebSocket
    // Note: Authentication will be triggered automatically by _onWebSocketConnected()
    await this.ws.connect();
  }

  /**
   * Send state update to server
   * @param {Object} state - Meeting state
   * @returns {Promise<void>}
   */
  async sendState(state) {
    if (!this.pairing.isAuthorized()) {
      throw new Error('Not authorized. Pairing required.');
    }

    const payload = {
      type: 'state',
      data: state
    };

    const message = await this._createSignedMessage(payload);
    await this.ws.send(message);
  }

  /**
   * Disconnect from server
   * @returns {Promise<void>}
   */
  async disconnect() {
    console.log('[StreamControllerClient] Disconnecting...');

    // Stop heartbeat
    this._stopHeartbeat();

    // Disconnect WebSocket
    await this.ws.disconnect();
  }

  /**
   * Register event handler
   * Events: 'connected', 'command', 'pairing-required', 'disconnected', 'error'
   * @param {string} event - Event name
   * @param {Function} handler - Event handler
   */
  on(event, handler) {
    if (!this.eventHandlers[event]) {
      this.eventHandlers[event] = [];
    }
    this.eventHandlers[event].push(handler);
  }

  /**
   * Remove event handler
   * @param {string} event - Event name
   * @param {Function} handler - Event handler to remove
   */
  off(event, handler) {
    if (!this.eventHandlers[event]) {
      return;
    }

    const index = this.eventHandlers[event].indexOf(handler);
    if (index > -1) {
      this.eventHandlers[event].splice(index, 1);
    }
  }

  /**
   * Get current connection state
   * @returns {Object} State object
   */
  getState() {
    return {
      connected: this.ws.isConnected(),
      authorized: this.pairing.isAuthorized(),
      pairingPending: this.pairing.isPending()
    };
  }

  /**
   * Force re-pairing (regenerates keys)
   * @returns {Promise<void>}
   */
  async repair() {
    console.log('[StreamControllerClient] Re-pairing...');

    await this.auth.reset();
    await this.pairing.reset();
    await this.connect();
  }

  // ========== Internal Methods ==========

  /**
   * Setup internal event handlers for all managers
   * @private
   */
  _setupEventHandlers() {
    // WebSocket events
    this.ws.on('connected', () => this._onWebSocketConnected());
    this.ws.on('disconnected', (reason) => this._onWebSocketDisconnected(reason));
    this.ws.on('message', (msg) => this._handleServerMessage(msg));
    this.ws.on('error', (error) => this._emit('error', error));

    // Pairing events
    this.pairing.on('authorized', () => this._onPairingAuthorized());
    this.pairing.on('pending', () => this._emit('pairing-required'));
    this.pairing.on('denied', () => {
      this._emit('error', new Error('Pairing denied by user'));
    });
    this.pairing.on('timeout', () => {
      this._emit('error', new Error('Pairing request timed out'));
    });
  }

  /**
   * Handle WebSocket connected event
   * @private
   */
  async _onWebSocketConnected() {
    console.log('[StreamControllerClient] WebSocket connected');

    // Trigger authentication/pairing flow
    // This handles both initial connection and reconnections
    try {
      await this.pairing.authenticate(this.ws);
    } catch (error) {
      console.error('[StreamControllerClient] Error during authentication:', error);
      this._emit('error', error);
    }
  }

  /**
   * Handle WebSocket disconnected event
   * @private
   */
  _onWebSocketDisconnected(reason) {
    console.log('[StreamControllerClient] Disconnected:', reason);

    // Stop heartbeat
    this._stopHeartbeat();

    // Mark as unauthorized (will need to re-authenticate on reconnect)
    this.pairing.markUnauthorized();

    // Emit disconnected event
    this._emit('disconnected', reason);
  }

  /**
   * Handle pairing authorized event
   * @private
   */
  _onPairingAuthorized() {
    console.log('[StreamControllerClient] Authorized!');

    // Start heartbeat
    this._startHeartbeat();

    // Emit connected event
    this._emit('connected');
  }

  /**
   * Handle message from server
   * @param {Object} message - Server message
   * @private
   */
  async _handleServerMessage(message) {
    switch (message.type) {
      case 'command':
        this._emit('command', {
          action: message.action,
          data: message.data
        });
        break;

      case 'error':
        await this._handleServerError(message);
        break;

      case 'heartbeat_ack':
        // Heartbeat acknowledged, nothing to do
        break;

      // Let pairing manager handle auth-related messages
      case 'handshake_success':
      case 'handshake_pending':
      case 'handshake_denied':
      case 'handshake_timeout':
        this.pairing.handleMessage(message);
        break;

      default:
        console.warn('[StreamControllerClient] Unknown message type:', message.type);
    }
  }

  /**
   * Handle error from server
   * @param {Object} message - Error message
   * @private
   */
  async _handleServerError(message) {
    console.error('[StreamControllerClient] Server error:', message.error_code, message.message);

    if (message.error_code === 'not_authorized' ||
        message.error_code === 'invalid_signature') {
      // Need to re-authorize
      console.log('[StreamControllerClient] Re-authorization required');

      this.pairing.markUnauthorized();
      this._stopHeartbeat();

      // Try to re-authenticate
      await this.pairing.authenticate(this.ws);
    } else {
      // Other error
      this._emit('error', new Error(`Server error: ${message.message}`));
    }
  }

  /**
   * Create signed message with JWT
   * @param {Object} payload - Message payload
   * @returns {Promise<Object>} Complete message with signature
   * @private
   */
  async _createSignedMessage(payload) {
    const token = await this.auth.signMessage(payload);

    return {
      type: payload.type,
      extension_id: this.extensionId,
      instance_id: this.auth.getInstanceId(),
      data: payload.data,
      token: token
    };
  }

  /**
   * Start sending heartbeats
   * @private
   */
  _startHeartbeat() {
    if (this.heartbeatTimer) {
      return;  // Already running
    }

    console.log('[StreamControllerClient] Starting heartbeat');

    this.heartbeatTimer = setInterval(async () => {
      if (!this.ws.isConnected() || !this.pairing.isAuthorized()) {
        return;
      }

      try {
        // Create heartbeat payload (empty for now, can add data later)
        const payload = {
          type: 'heartbeat',
          data: {}
        };

        const message = await this._createSignedMessage(payload);
        await this.ws.send(message);
      } catch (error) {
        console.error('[StreamControllerClient] Error sending heartbeat:', error);
      }
    }, this.heartbeatInterval);
  }

  /**
   * Stop sending heartbeats
   * @private
   */
  _stopHeartbeat() {
    if (this.heartbeatTimer) {
      console.log('[StreamControllerClient] Stopping heartbeat');
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * Emit event to registered handlers
   * @param {string} event - Event name
   * @param {*} data - Event data
   * @private
   */
  _emit(event, data) {
    const handlers = this.eventHandlers[event] || [];
    handlers.forEach(handler => {
      try {
        handler(data);
      } catch (error) {
        console.error(`[StreamControllerClient] Error in ${event} handler:`, error);
      }
    });
  }
}
