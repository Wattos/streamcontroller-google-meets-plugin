/**
 * Pairing Manager
 *
 * Handles the pairing state machine and authentication flow
 */

import { MetadataCollector } from './metadata-collector.js';

export class PairingManager {
  constructor(extensionId, authManager) {
    this.extensionId = extensionId;
    this.auth = authManager;
    this.state = 'unauthorized';  // unauthorized, pending, authorized
    this.eventHandlers = {};
  }

  /**
   * Start authentication/pairing flow
   * @param {WebSocketManager} wsManager - WebSocket manager instance
   */
  async authenticate(wsManager) {
    console.log('[PairingManager] Starting authentication');

    // Collect metadata
    const metadata = await MetadataCollector.getMetadata();

    // Get public key
    const publicKey = await this.auth.getPublicKey();

    // Send pairing request
    await wsManager.send({
      type: 'handshake',
      extension_id: this.extensionId,
      instance_id: this.auth.getInstanceId(),
      public_key: publicKey,
      metadata: metadata
    });

    this.state = 'pending';
    console.log('[PairingManager] Pairing request sent');
  }

  /**
   * Handle message from server related to pairing
   * @param {Object} message - Server message
   */
  handleMessage(message) {
    switch (message.type) {
      case 'handshake_success':
        console.log('[PairingManager] Pairing approved!');
        this.state = 'authorized';
        this._emit('authorized');
        break;

      case 'handshake_pending':
        console.log('[PairingManager] Waiting for user approval...');
        this.state = 'pending';
        this._emit('pending');
        break;

      case 'handshake_denied':
        console.error('[PairingManager] Pairing denied by user');
        this.state = 'unauthorized';
        this._emit('denied');
        break;

      case 'handshake_timeout':
        console.error('[PairingManager] Pairing request timed out');
        this.state = 'unauthorized';
        this._emit('timeout');
        break;
    }
  }

  /**
   * Check if currently authorized
   * @returns {boolean}
   */
  isAuthorized() {
    return this.state === 'authorized';
  }

  /**
   * Check if pairing is pending
   * @returns {boolean}
   */
  isPending() {
    return this.state === 'pending';
  }

  /**
   * Mark as unauthorized (for re-pairing)
   */
  markUnauthorized() {
    this.state = 'unauthorized';
  }

  /**
   * Reset pairing state
   */
  reset() {
    this.state = 'unauthorized';
  }

  /**
   * Register event handler
   * Events: 'authorized', 'pending', 'denied', 'timeout'
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
        console.error(`[PairingManager] Error in ${event} handler:`, error);
      }
    });
  }
}
