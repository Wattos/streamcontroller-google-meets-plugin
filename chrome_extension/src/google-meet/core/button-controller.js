/**
 * Button Controller
 *
 * Generic controller pattern for Google Meet toggle buttons (mic, camera, hand)
 * Handles state detection and toggle actions in a reusable way
 */

import { clickElement, findButtonByLabel } from './dom-utils.js';

export class ButtonController {
  /**
   * Create a button controller
   * @param {Object} config - Configuration object
   * @param {string} config.selector - CSS selector for the button
   * @param {string[]} config.keywords - Keywords to find button by aria-label
   * @param {string[]} config.onIndicators - Text indicating button is "on" state
   */
  constructor(config) {
    this.selector = config.selector;
    this.keywords = config.keywords;
    this.onIndicators = config.onIndicators;
  }

  /**
   * Find the button element
   * @returns {Element|null} Button element or null
   */
  findButton() {
    // Try direct selector first
    let button = document.querySelector(this.selector);
    if (button) return button;

    // Fallback to keyword search
    return findButtonByLabel(this.keywords);
  }

  /**
   * Get current state of the button
   * @returns {boolean} True if button is in "on" state
   */
  getState() {
    const button = this.findButton();
    if (!button) return false;

    // Get label from aria-label or data-tooltip
    const label = (
      button.getAttribute('aria-label') ||
      button.getAttribute('data-tooltip') ||
      ''
    ).toLowerCase();

    // Check if any of the "on" indicators are present
    return this.onIndicators.some(indicator =>
      label.includes(indicator.toLowerCase())
    );
  }

  /**
   * Toggle the button
   * @throws {Error} If button not found
   */
  async toggle() {
    const button = this.findButton();

    if (!button) {
      throw new Error(`Button not found (keywords: ${this.keywords.join(', ')})`);
    }

    console.log(`[ButtonController] Clicking button: ${this.keywords[0]}`);
    clickElement(button);
  }
}
