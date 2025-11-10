/**
 * Hand Raising Control
 *
 * Handles hand raise state detection and toggle for Google Meet
 */

import { ButtonController } from './core/button-controller.js';

// Hand-specific configuration
const SELECTOR = '[aria-label*="hand" i], [data-tooltip*="hand" i]';
const KEYWORDS = ['hand', 'raise'];
const ON_INDICATORS = ['lower']; // Button says "lower hand" when hand is raised

// Create controller instance
const handController = new ButtonController({
  selector: SELECTOR,
  keywords: KEYWORDS,
  onIndicators: ON_INDICATORS
});

/**
 * Get current hand raise state
 * @returns {boolean} True if hand is raised
 */
export function getHandState() {
  return handController.getState();
}

/**
 * Toggle hand raise on/off
 * @returns {Promise<void>}
 * @throws {Error} If hand button not found
 */
export async function toggleHand() {
  await handController.toggle();
}
