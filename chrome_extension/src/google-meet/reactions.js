/**
 * Reactions
 *
 * Handles sending emoji reactions in Google Meet
 */

import { clickElement, findButtonByLabel } from './core/dom-utils.js';

// Reaction-specific selectors
const REACTIONS_BUTTON_SELECTOR = '[aria-label*="reaction" i], [data-tooltip*="reaction" i]';
const REACTIONS_BUTTON_KEYWORDS = ['reaction', 'send a reaction'];

const REACTION_EMOJI_SELECTORS = {
  sparkling_heart: 'button[aria-label*="💖"], button[data-emoji="💖"]',
  thumbs_up: 'button[aria-label*="👍"], button[data-emoji="👍"]',
  celebrate: 'button[aria-label*="🎉"], button[data-emoji="🎉"]',
  applause: 'button[aria-label*="👏"], button[data-emoji="👏"]',
  laugh: 'button[aria-label*="😂"], button[data-emoji="😂"]',
  surprised: 'button[aria-label*="😮"], button[data-emoji="😮"]',
  sad: 'button[aria-label*="😢"], button[data-emoji="😢"]',
  thinking: 'button[aria-label*="🤔"], button[data-emoji="🤔"]',
  thumbs_down: 'button[aria-label*="👎"], button[data-emoji="👎"]'
};

/**
 * Send a reaction in the meeting
 * @param {string} reactionType - Type of reaction (sparkling_heart, thumbs_up, celebrate, applause, laugh, surprised, sad, thinking, thumbs_down)
 * @returns {Promise<void>}
 * @throws {Error} If reaction button or emoji not found
 */
export async function sendReaction(reactionType) {
  if (!reactionType) {
    throw new Error('No reaction type specified');
  }

  console.log('[Reactions] Sending reaction:', reactionType);

  // Find and click reactions button
  const reactionsButton =
    document.querySelector(REACTIONS_BUTTON_SELECTOR) ||
    findButtonByLabel(REACTIONS_BUTTON_KEYWORDS);

  if (!reactionsButton) {
    throw new Error('Reactions button not found');
  }

  clickElement(reactionsButton);

  // Wait for menu to appear
  await new Promise(resolve => setTimeout(resolve, 300));

  // Find specific reaction emoji
  const emojiSelector = REACTION_EMOJI_SELECTORS[reactionType];
  if (!emojiSelector) {
    throw new Error(`Unknown reaction type: ${reactionType}`);
  }

  let emojiButton = document.querySelector(emojiSelector);

  // Fallback: search by reaction type in aria-label
  if (!emojiButton) {
    const allEmojis = document.querySelectorAll('[role="button"][aria-label*="emoji"]');
    for (const emoji of allEmojis) {
      const label = emoji.getAttribute('aria-label');
      if (label && label.includes(reactionType.replace('_', ' '))) {
        emojiButton = emoji;
        break;
      }
    }
  }

  if (!emojiButton) {
    throw new Error(`Reaction emoji not found: ${reactionType}`);
  }

  clickElement(emojiButton);
  console.log('[Reactions] Reaction sent:', reactionType);
}
