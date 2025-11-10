/**
 * Authentication Manager
 *
 * Handles cryptographic operations:
 * - ECDSA P-256 keypair generation and storage
 * - JWS (JSON Web Signature) creation with ES256
 * - Instance ID management
 */

export class AuthManager {
  constructor() {
    this.privateKey = null;
    this.publicKeyJWK = null;
    this.instanceId = null;
  }

  /**
   * Initialize authentication (load or generate keys)
   */
  async initialize() {
    // Get or create instance ID
    this.instanceId = await this._getOrCreateInstanceId();

    // Try to load existing keypair
    const keyPair = await this._loadKeyPair();

    if (keyPair) {
      this.privateKey = keyPair.privateKey;
      this.publicKeyJWK = keyPair.publicKeyJWK;
      console.log('[AuthManager] Loaded existing keypair');
    } else {
      // No existing keys, generate new ones
      await this._generateKeyPair();
      console.log('[AuthManager] Generated new keypair');
    }
  }

  /**
   * Get or create instance ID (persists across browser restarts)
   */
  async _getOrCreateInstanceId() {
    const result = await chrome.storage.local.get('instance_id');

    if (result.instance_id) {
      return result.instance_id;
    }

    // Generate new instance ID
    const instanceId = crypto.randomUUID();
    await chrome.storage.local.set({ instance_id: instanceId });

    return instanceId;
  }

  /**
   * Generate new ECDSA P-256 keypair
   */
  async _generateKeyPair() {
    // Generate keypair
    const keyPair = await crypto.subtle.generateKey(
      {
        name: "ECDSA",
        namedCurve: "P-256"
      },
      true,  // extractable
      ["sign", "verify"]
    );

    this.privateKey = keyPair.privateKey;

    // Export public key as JWK for transmission
    this.publicKeyJWK = await crypto.subtle.exportKey("jwk", keyPair.publicKey);

    // Store keys
    await this._saveKeyPair();
  }

  /**
   * Load keypair from storage
   */
  async _loadKeyPair() {
    try {
      // Load public key JWK from chrome.storage
      const result = await chrome.storage.local.get('public_key_jwk');

      if (!result.public_key_jwk) {
        return null;
      }

      this.publicKeyJWK = result.public_key_jwk;

      // Load private key from IndexedDB
      this.privateKey = await this._loadPrivateKeyFromIndexedDB();

      if (!this.privateKey) {
        console.warn('[AuthManager] Public key found but no private key, regenerating');
        return null;
      }

      return {
        privateKey: this.privateKey,
        publicKeyJWK: this.publicKeyJWK
      };
    } catch (error) {
      console.error('[AuthManager] Error loading keypair:', error);
      return null;
    }
  }

  /**
   * Save keypair to storage
   */
  async _saveKeyPair() {
    // Save public key JWK to chrome.storage
    await chrome.storage.local.set({
      public_key_jwk: this.publicKeyJWK
    });

    // Save private key to IndexedDB (more secure, can't be easily exported)
    await this._savePrivateKeyToIndexedDB(this.privateKey);
  }

  /**
   * Save private key to IndexedDB
   */
  async _savePrivateKeyToIndexedDB(privateKey) {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('StreamControllerAuth', 1);

      request.onerror = () => reject(request.error);

      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        if (!db.objectStoreNames.contains('keys')) {
          db.createObjectStore('keys');
        }
      };

      request.onsuccess = async () => {
        const db = request.result;
        const transaction = db.transaction(['keys'], 'readwrite');
        const store = transaction.objectStore('keys');

        // Export as non-extractable format (JWK)
        const jwk = await crypto.subtle.exportKey('jwk', privateKey);

        store.put(jwk, 'private_key');

        transaction.oncomplete = () => {
          db.close();
          resolve();
        };

        transaction.onerror = () => reject(transaction.error);
      };
    });
  }

  /**
   * Load private key from IndexedDB
   */
  async _loadPrivateKeyFromIndexedDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('StreamControllerAuth', 1);

      request.onerror = () => reject(request.error);

      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        if (!db.objectStoreNames.contains('keys')) {
          db.createObjectStore('keys');
        }
      };

      request.onsuccess = async () => {
        const db = request.result;

        if (!db.objectStoreNames.contains('keys')) {
          db.close();
          resolve(null);
          return;
        }

        const transaction = db.transaction(['keys'], 'readonly');
        const store = transaction.objectStore('keys');
        const getRequest = store.get('private_key');

        getRequest.onsuccess = async () => {
          const jwk = getRequest.result;

          if (!jwk) {
            db.close();
            resolve(null);
            return;
          }

          try {
            // Import JWK as CryptoKey
            const privateKey = await crypto.subtle.importKey(
              'jwk',
              jwk,
              {
                name: 'ECDSA',
                namedCurve: 'P-256'
              },
              false,  // not extractable
              ['sign']
            );

            db.close();
            resolve(privateKey);
          } catch (error) {
            console.error('[AuthManager] Error importing private key:', error);
            db.close();
            resolve(null);
          }
        };

        getRequest.onerror = () => {
          db.close();
          reject(getRequest.error);
        };
      };
    });
  }

  /**
   * Create JWS token (JSON Web Signature with ES256)
   * @param {Object} payload - Data to sign
   * @returns {Promise<string>} JWT token
   */
  async signMessage(payload) {
    if (!this.privateKey) {
      throw new Error('No private key available');
    }

    // Add standard JWT claims
    const fullPayload = {
      ...payload,
      iat: Math.floor(Date.now() / 1000),  // Issued at
      exp: Math.floor(Date.now() / 1000) + 300,  // Expires in 5 minutes
      instance_id: this.instanceId
    };

    // Create JWT header
    const header = {
      alg: 'ES256',
      typ: 'JWT'
    };

    // Encode header and payload
    const encodedHeader = this._base64UrlEncode(JSON.stringify(header));
    const encodedPayload = this._base64UrlEncode(JSON.stringify(fullPayload));

    // Create signature input
    const signatureInput = `${encodedHeader}.${encodedPayload}`;
    const encoder = new TextEncoder();
    const data = encoder.encode(signatureInput);

    // Sign with private key
    const signature = await crypto.subtle.sign(
      {
        name: 'ECDSA',
        hash: 'SHA-256'
      },
      this.privateKey,
      data
    );

    // Encode signature
    const encodedSignature = this._base64UrlEncode(signature);

    // Return complete JWT
    return `${encodedHeader}.${encodedPayload}.${encodedSignature}`;
  }

  /**
   * Get public key (for transmission to server)
   */
  async getPublicKey() {
    return this.publicKeyJWK;
  }

  /**
   * Get instance ID
   */
  getInstanceId() {
    return this.instanceId;
  }

  /**
   * Reset keys (delete and regenerate)
   */
  async reset() {
    await this._deleteKeyPair();
    await this._generateKeyPair();
    console.log('[AuthManager] Keys reset');
  }

  /**
   * Delete keypair from storage
   */
  async _deleteKeyPair() {
    // Delete from chrome.storage
    await chrome.storage.local.remove('public_key_jwk');

    // Delete from IndexedDB
    await this._deletePrivateKeyFromIndexedDB();
  }

  /**
   * Delete private key from IndexedDB
   */
  async _deletePrivateKeyFromIndexedDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('StreamControllerAuth', 1);

      request.onerror = () => reject(request.error);

      request.onsuccess = () => {
        const db = request.result;

        if (!db.objectStoreNames.contains('keys')) {
          db.close();
          resolve();
          return;
        }

        const transaction = db.transaction(['keys'], 'readwrite');
        const store = transaction.objectStore('keys');
        store.delete('private_key');

        transaction.oncomplete = () => {
          db.close();
          resolve();
        };

        transaction.onerror = () => {
          db.close();
          reject(transaction.error);
        };
      };
    });
  }

  /**
   * Base64 URL encode (RFC 4648)
   * @param {string|ArrayBuffer} data - Data to encode
   * @returns {string} Base64 URL encoded string
   * @private
   */
  _base64UrlEncode(data) {
    let base64;

    if (data instanceof ArrayBuffer) {
      // Convert ArrayBuffer to base64
      const bytes = new Uint8Array(data);
      let binary = '';
      for (let i = 0; i < bytes.length; i++) {
        binary += String.fromCharCode(bytes[i]);
      }
      base64 = btoa(binary);
    } else {
      // Assume string
      base64 = btoa(data);
    }

    // Convert to URL-safe format
    return base64
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '');
  }
}
