/**
 * DOM Observer
 *
 * Centralized MutationObserver for efficiently watching Google Meet UI changes
 */

import { debounce } from './dom-utils.js';

class MeetObserver {
  constructor() {
    this.observer = null;
    this.callback = null;
    this.isObserving = false;
  }

  /**
   * Start observing DOM changes
   * @param {Function} callback - Function to call when relevant changes detected
   */
  startObserving(callback) {
    if (this.isObserving) {
      console.warn('[MeetObserver] Already observing');
      return;
    }

    this.callback = debounce(callback, 500);

    this.observer = new MutationObserver(() => {
      if (this.callback) {
        this.callback();
      }
    });

    // Observe the entire meeting UI for relevant attribute changes
    this.observer.observe(document.body, {
      attributes: true,
      attributeFilter: ['aria-label', 'data-tooltip', 'aria-pressed'],
      subtree: true
    });

    this.isObserving = true;
    console.log('[MeetObserver] Started observing');
  }

  /**
   * Stop observing DOM changes
   */
  stopObserving() {
    if (this.observer) {
      this.observer.disconnect();
      this.observer = null;
    }

    this.callback = null;
    this.isObserving = false;
    console.log('[MeetObserver] Stopped observing');
  }
}

// Export singleton instance
export const observer = new MeetObserver();
