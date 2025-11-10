/**
 * Meeting Information
 *
 * Handles meeting detection and metadata extraction for Google Meet
 */

import { waitForElement } from './core/dom-utils.js';

// Meeting detection selector - only matches when actually in a call
const LEAVE_BUTTON_SELECTOR = '[aria-label*="Leave call" i], [aria-label*="End call" i]';

/**
 * Wait for meeting to start/load
 * @param {number} timeout - Timeout in milliseconds (default: 5000)
 * @returns {Promise<boolean>} True if meeting detected
 */
export async function waitForMeeting(timeout = 5000) {
  try {
    await waitForElement(LEAVE_BUTTON_SELECTOR, timeout);
    console.log('[MeetingInfo] Meeting detected (Leave button present)');
    return true;
  } catch (error) {
    console.log('[MeetingInfo] Meeting not detected yet (no Leave button)');
    return false;
  }
}

/**
 * Check if currently in a meeting
 * Only returns true when Leave button is present (actually connected to call)
 * @returns {boolean} True if in meeting
 */
export function isInMeeting() {
  return document.querySelector(LEAVE_BUTTON_SELECTOR) !== null;
}

/**
 * Leave the current meeting
 * Clicks the Leave call button and handles host dialog if present
 * @returns {Promise<void>}
 */
export async function leaveCall() {
  const leaveButton = document.querySelector(LEAVE_BUTTON_SELECTOR);

  if (!leaveButton) {
    console.warn('[MeetingInfo] Leave button not found - not in meeting?');
    throw new Error('Not in a meeting');
  }

  console.log('[MeetingInfo] Clicking Leave button');
  leaveButton.click();

  // Wait for potential host dialog to appear (500ms should be enough)
  await new Promise(resolve => setTimeout(resolve, 500));

  // Check if "Just leave the call" dialog appeared (shown when hosting)
  const justLeaveButton = document.querySelector('[aria-label="Just leave the call"]');

  if (justLeaveButton) {
    console.log('[MeetingInfo] Host dialog detected, clicking "Just leave the call"');
    justLeaveButton.click();
  } else {
    console.log('[MeetingInfo] No host dialog, already left');
  }
}

/**
 * Extract meeting ID from URL or page metadata
 * @returns {string} Meeting ID or 'unknown'
 */
export function getMeetingId() {
  // Try URL first (format: meet.google.com/xxx-xxxx-xxx)
  const urlMatch = window.location.pathname.match(/\/([a-z]{3}-[a-z]{4}-[a-z]{3})/);
  if (urlMatch) {
    return urlMatch[1];
  }

  // Try from page metadata
  const metaElement = document.querySelector('[data-meeting-code], [data-call-id]');
  if (metaElement) {
    return metaElement.dataset.meetingCode || metaElement.dataset.callId;
  }

  return 'unknown';
}

/**
 * Get meeting name from page title or DOM
 * @returns {string} Meeting name
 */
export function getMeetingName() {
  // Try to extract from page title
  const title = document.title;
  if (title && title !== 'Google Meet' && !title.startsWith('Meet - ')) {
    // Extract meeting name from title (usually "Meeting Name - Google Meet")
    const match = title.match(/^(.+?)\s*[-|]\s*(?:Google\s+)?Meet/i);
    if (match && match[1]) {
      return match[1].trim();
    }
  }

  // Try to find meeting title in DOM
  const titleSelectors = [
    '[data-meeting-title]',
    '[data-call-title]',
    'h1[class*="title"]',
    'div[class*="meeting-title"]'
  ];

  for (const selector of titleSelectors) {
    const element = document.querySelector(selector);
    if (element) {
      const text = element.textContent?.trim();
      if (text && text.length > 0 && text !== 'Meet') {
        return text;
      }
    }
  }

  // Fallback to meeting ID
  const meetingId = getMeetingId();
  return meetingId !== 'unknown' ? meetingId : 'Unknown Meeting';
}

/**
 * Get participant count from UI
 * @returns {number} Number of participants
 */
export function getParticipantCount() {
  // Try to find participant count in various locations
  const selectors = [
    '[aria-label*="participant" i]',
    '[data-participant-count]',
    'div[class*="participant"] span[class*="count"]',
    'div[jsname] span:not([class])'
  ];

  for (const selector of selectors) {
    const elements = document.querySelectorAll(selector);
    for (const element of elements) {
      const text = element.textContent || element.getAttribute('aria-label') || '';

      // Look for patterns like "X participants", "X people", etc.
      const match = text.match(/(\d+)\s*(?:participant|people|person)/i);
      if (match && match[1]) {
        return parseInt(match[1], 10);
      }

      // Look for aria-label patterns
      if (element.hasAttribute('aria-label')) {
        const ariaLabel = element.getAttribute('aria-label');
        const ariaMatch = ariaLabel.match(/(\d+)\s*(?:participant|people|person)/i);
        if (ariaMatch && ariaMatch[1]) {
          return parseInt(ariaMatch[1], 10);
        }
      }
    }
  }

  // Try counting video tiles as fallback - count unique participant IDs
  const participantElements = document.querySelectorAll('[data-participant-id]');
  if (participantElements.length > 0) {
    // Use Set to get unique participant IDs (avoids double counting)
    const uniqueIds = new Set();
    participantElements.forEach(el => {
      const id = el.getAttribute('data-participant-id');
      if (id) {
        uniqueIds.add(id);
      }
    });
    return uniqueIds.size;
  }

  return 0;
}
