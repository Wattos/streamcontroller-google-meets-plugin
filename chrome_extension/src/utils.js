/**
 * Utility functions for Google Meet StreamController Bridge
 */

/**
 * Compute HMAC-SHA256 signature for message authentication
 * @param {string} message - Message to sign
 * @param {string} key - Session key
 * @returns {Promise<string>} Hex-encoded HMAC signature
 */
async function computeHMAC(message, key) {
  const encoder = new TextEncoder();
  const keyData = encoder.encode(key);
  const messageData = encoder.encode(message);

  // Import key for HMAC
  const cryptoKey = await crypto.subtle.importKey(
    'raw',
    keyData,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );

  // Sign the message
  const signature = await crypto.subtle.sign('HMAC', cryptoKey, messageData);

  // Convert to hex string
  return Array.from(new Uint8Array(signature))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

/**
 * Create a signed message with HMAC
 * @param {object} message - Message object (without hmac field)
 * @param {string} sessionKey - Session key for signing
 * @returns {Promise<object>} Message with hmac field
 */
async function signMessage(message, sessionKey) {
  // Create message string without hmac field
  const messageStr = JSON.stringify(message, Object.keys(message).sort());

  // Compute HMAC
  const hmac = await computeHMAC(messageStr, sessionKey);

  // Return message with hmac
  return { ...message, hmac };
}

/**
 * Generate a unique extension ID
 * @returns {string} Extension ID
 */
function getExtensionId() {
  // Use Chrome extension ID if available
  if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.id) {
    return chrome.runtime.id;
  }

  // Fallback to stored ID or generate new one
  const stored = localStorage.getItem('streamcontroller_extension_id');
  if (stored) {
    return stored;
  }

  const newId = 'ext_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
  localStorage.setItem('streamcontroller_extension_id', newId);
  return newId;
}

/**
 * Log with timestamp
 * @param {string} level - Log level (info, warn, error)
 * @param {string} message - Log message
 * @param {any} data - Optional data to log
 */
function log(level, message, data = null) {
  const timestamp = new Date().toISOString();
  const prefix = `[GoogleMeet Bridge ${timestamp}]`;

  if (data) {
    console[level](`${prefix} ${message}`, data);
  } else {
    console[level](`${prefix} ${message}`);
  }
}

/**
 * Wait for element to appear in DOM
 * @param {string} selector - CSS selector
 * @param {number} timeout - Timeout in ms
 * @returns {Promise<Element>} Found element
 */
function waitForElement(selector, timeout = 10000) {
  return new Promise((resolve, reject) => {
    const element = document.querySelector(selector);
    if (element) {
      resolve(element);
      return;
    }

    const observer = new MutationObserver((mutations, obs) => {
      const element = document.querySelector(selector);
      if (element) {
        obs.disconnect();
        clearTimeout(timeoutId);
        resolve(element);
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    const timeoutId = setTimeout(() => {
      observer.disconnect();
      reject(new Error(`Element ${selector} not found within ${timeout}ms`));
    }, timeout);
  });
}

/**
 * Debounce function to limit rapid calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in ms
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    computeHMAC,
    signMessage,
    getExtensionId,
    log,
    waitForElement,
    debounce
  };
}
