/**
 * Metadata Collector
 *
 * Collects browser and extension metadata for user-friendly pairing displays
 */

export class MetadataCollector {
  /**
   * Get complete metadata for pairing request
   * @returns {Promise<Object>} Metadata object with extension and browser info
   */
  static async getMetadata() {
    const manifest = chrome.runtime.getManifest();

    return {
      extension_name: manifest.name,
      extension_version: manifest.version,
      browser_name: this._getBrowserName(),
      browser_version: this._getBrowserVersion(),
      os: this._getOS(),
      timestamp: Date.now()
    };
  }

  /**
   * Detect browser name from user agent
   * @returns {string} Browser name
   * @private
   */
  static _getBrowserName() {
    const userAgent = navigator.userAgent;

    // Check for Edge first (contains Chrome in UA)
    if (userAgent.includes('Edg/')) {
      return 'Microsoft Edge';
    }
    // Check for Chrome
    else if (userAgent.includes('Chrome/')) {
      return 'Google Chrome';
    }
    // Check for Firefox
    else if (userAgent.includes('Firefox/')) {
      return 'Mozilla Firefox';
    }
    // Check for Safari (must not contain Chrome)
    else if (userAgent.includes('Safari/') && !userAgent.includes('Chrome')) {
      return 'Safari';
    }
    // Check for Opera
    else if (userAgent.includes('OPR/') || userAgent.includes('Opera/')) {
      return 'Opera';
    }
    else {
      return 'Unknown Browser';
    }
  }

  /**
   * Extract browser version from user agent
   * @returns {string} Browser version
   * @private
   */
  static _getBrowserVersion() {
    const userAgent = navigator.userAgent;

    // Try different patterns for different browsers
    const patterns = [
      { regex: /Edg\/([\d.]+)/, name: 'Edge' },
      { regex: /Chrome\/([\d.]+)/, name: 'Chrome' },
      { regex: /Firefox\/([\d.]+)/, name: 'Firefox' },
      { regex: /Version\/([\d.]+)/, name: 'Safari' },
      { regex: /OPR\/([\d.]+)/, name: 'Opera' }
    ];

    for (const { regex } of patterns) {
      const match = userAgent.match(regex);
      if (match && match[1]) {
        return match[1];
      }
    }

    return 'Unknown';
  }

  /**
   * Detect operating system from user agent
   * @returns {string} OS name
   * @private
   */
  static _getOS() {
    const userAgent = navigator.userAgent;
    const platform = navigator.platform;

    // Windows detection
    if (userAgent.includes('Win')) {
      if (userAgent.includes('Windows NT 10.0')) {
        return 'Windows 10/11';
      } else if (userAgent.includes('Windows NT 6.3')) {
        return 'Windows 8.1';
      } else if (userAgent.includes('Windows NT 6.2')) {
        return 'Windows 8';
      } else if (userAgent.includes('Windows NT 6.1')) {
        return 'Windows 7';
      }
      return 'Windows';
    }
    // macOS detection
    else if (userAgent.includes('Mac')) {
      // Try to extract macOS version
      const match = userAgent.match(/Mac OS X ([\d_]+)/);
      if (match) {
        const version = match[1].replace(/_/g, '.');
        return `macOS ${version}`;
      }
      return 'macOS';
    }
    // Linux detection
    else if (userAgent.includes('Linux')) {
      if (userAgent.includes('Ubuntu')) return 'Ubuntu Linux';
      if (userAgent.includes('Fedora')) return 'Fedora Linux';
      if (userAgent.includes('Debian')) return 'Debian Linux';
      return 'Linux';
    }
    // Mobile OS detection
    else if (userAgent.includes('Android')) {
      const match = userAgent.match(/Android ([\d.]+)/);
      if (match) {
        return `Android ${match[1]}`;
      }
      return 'Android';
    }
    else if (userAgent.includes('iOS') || (userAgent.includes('iPhone') || userAgent.includes('iPad'))) {
      return 'iOS';
    }
    // ChromeOS
    else if (userAgent.includes('CrOS')) {
      return 'ChromeOS';
    }

    // Fallback to platform
    return platform || 'Unknown OS';
  }
}
