/**
 * WebSocket Manager
 *
 * Handles WebSocket connection, reconnection, and message passing
 */

export class WebSocketManager {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.eventHandlers = {};
    this.reconnectTimer = null;
    this.reconnectDelay = 5000;  // 5 seconds
    this.shouldReconnect = true;
  }

  /**
   * Connect to WebSocket server
   * @returns {Promise<void>}
   */
  async connect() {
    return new Promise((resolve, reject) => {
      console.log('[WebSocketManager] Connecting to', this.url);

      try {
        this.ws = new WebSocket(this.url);
      } catch (error) {
        reject(error);
        return;
      }

      this.ws.onopen = () => {
        console.log('[WebSocketManager] Connected');
        this._emit('connected');
        resolve();
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this._emit('message', message);
        } catch (error) {
          console.error('[WebSocketManager] Error parsing message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('[WebSocketManager] WebSocket error:', error);
        this._emit('error', error);
      };

      this.ws.onclose = (event) => {
        console.log('[WebSocketManager] Connection closed:', event.code, event.reason);
        this._emit('disconnected', event.reason || 'connection closed');

        // Schedule reconnection if enabled
        if (this.shouldReconnect) {
          this._scheduleReconnect();
        }
      };

      // Timeout for connection
      setTimeout(() => {
        if (this.ws.readyState !== WebSocket.OPEN) {
          reject(new Error('Connection timeout'));
          this.ws.close();
        }
      }, 10000);  // 10 second timeout
    });
  }

  /**
   * Send message through WebSocket
   * @param {Object} message - Message object
   * @returns {Promise<void>}
   */
  async send(message) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected');
    }

    this.ws.send(JSON.stringify(message));
  }

  /**
   * Disconnect from WebSocket
   */
  async disconnect() {
    console.log('[WebSocketManager] Disconnecting');

    // Disable auto-reconnect
    this.shouldReconnect = false;

    // Clear reconnect timer
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    // Close connection
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Check if WebSocket is connected
   * @returns {boolean}
   */
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Enable auto-reconnect
   */
  enableReconnect() {
    this.shouldReconnect = true;
  }

  /**
   * Disable auto-reconnect
   */
  disableReconnect() {
    this.shouldReconnect = false;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * Register event handler
   * Events: 'connected', 'message', 'disconnected', 'error'
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
        console.error(`[WebSocketManager] Error in ${event} handler:`, error);
      }
    });
  }

  /**
   * Schedule automatic reconnection
   * @private
   */
  _scheduleReconnect() {
    if (this.reconnectTimer) {
      return;  // Already scheduled
    }

    console.log(`[WebSocketManager] Reconnecting in ${this.reconnectDelay / 1000}s...`);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;

      console.log('[WebSocketManager] Attempting to reconnect...');
      this.connect().catch(error => {
        console.error('[WebSocketManager] Reconnection failed:', error);
      });
    }, this.reconnectDelay);
  }
}
