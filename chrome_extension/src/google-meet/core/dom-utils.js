/**
 * DOM Utilities
 *
 * Shared DOM manipulation and query utilities for Google Meet interactions
 */

/**
 * Wait for an element to appear in the DOM
 * @param {string} selector - CSS selector
 * @param {number} timeout - Timeout in milliseconds (default: 5000)
 * @returns {Promise<Element>} The found element
 */
export function waitForElement(selector, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const element = document.querySelector(selector);
    if (element) {
      resolve(element);
      return;
    }

    const observer = new MutationObserver(() => {
      const element = document.querySelector(selector);
      if (element) {
        observer.disconnect();
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
      reject(new Error(`Element not found: ${selector}`));
    }, timeout);
  });
}

/**
 * Debounce a function call
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
export function debounce(func, wait) {
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

/**
 * Safely click an element with error handling
 * @param {Element} element - Element to click
 * @throws {Error} If element is not clickable
 */
export function clickElement(element) {
  if (!element) {
    throw new Error('Cannot click: element is null');
  }

  if (!element.click) {
    throw new Error('Cannot click: element does not have click method');
  }

  element.click();
}

/**
 * Find button by keywords in aria-label
 * @param {string[]} keywords - Array of keywords to search for
 * @returns {Element|null} Found button or null
 */
export function findButtonByLabel(keywords) {
  const buttons = document.querySelectorAll('button[aria-label]');

  for (const button of buttons) {
    const label = (button.getAttribute('aria-label') || '').toLowerCase();

    // Check if label contains any of the keywords
    if (keywords.some(keyword => label.includes(keyword.toLowerCase()))) {
      return button;
    }
  }

  return null;
}
