/**
 * Camera Control
 *
 * Handles camera state detection and toggle for Google Meet
 */

import { ButtonController } from './core/button-controller.js';

// Camera-specific configuration
const SELECTOR = '[data-tooltip*="camera" i], [aria-label*="camera" i], button[jsname][aria-label*="camera"]';
const KEYWORDS = ['camera', 'video'];
const ON_INDICATORS = ['turn off']; // Button says "turn off camera" when camera is ON

// Create controller instance
const cameraController = new ButtonController({
  selector: SELECTOR,
  keywords: KEYWORDS,
  onIndicators: ON_INDICATORS
});

/**
 * Get current camera state
 * @returns {boolean} True if camera is enabled
 */
export function getCameraState() {
  return cameraController.getState();
}

/**
 * Toggle camera on/off
 * @returns {Promise<void>}
 * @throws {Error} If camera button not found
 */
export async function toggleCamera() {
  await cameraController.toggle();
}
