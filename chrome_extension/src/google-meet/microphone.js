/**
 * Microphone Control
 *
 * Handles microphone state detection and toggle for Google Meet
 */

import { ButtonController } from './core/button-controller.js';

// Microphone-specific configuration
const SELECTOR = 'button[data-is-muted]';
const KEYWORDS = ['microphone', 'mic', 'mute'];
const ON_INDICATORS = ['turn off', 'mute']; // Excludes 'unmute' which means mic is OFF

// Create controller instance
const micController = new ButtonController({
  selector: SELECTOR,
  keywords: KEYWORDS,
  onIndicators: ON_INDICATORS
});

/**
 * Get current microphone state
 * @returns {boolean} True if microphone is enabled
 */
export function getMicrophoneState() {
  return micController.getState();
}

/**
 * Toggle microphone on/off
 * @returns {Promise<void>}
 * @throws {Error} If microphone button not found
 */
export async function toggleMicrophone() {
  await micController.toggle();
}
