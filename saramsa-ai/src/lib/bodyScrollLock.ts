/**
 * Body Scroll Lock Utilities
 * Prevents body scrolling when modals or overlays are open
 */

let scrollLockCount = 0;
let originalOverflow = '';
let originalPaddingRight = '';

/**
 * Locks body scroll and prevents background scrolling
 */
export function lockBodyScroll(): void {
  if (typeof document === 'undefined') return;

  scrollLockCount++;

  if (scrollLockCount === 1) {
    const body = document.body;

    // Store original values
    originalOverflow = body.style.overflow;
    originalPaddingRight = body.style.paddingRight;

    // Get scrollbar width to prevent layout shift
    const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;

    // Apply scroll lock
    body.style.overflow = 'hidden';

    // Add padding to compensate for scrollbar removal
    if (scrollbarWidth > 0) {
      body.style.paddingRight = `${scrollbarWidth}px`;
    }
  }
}

/**
 * Unlocks body scroll when all modals/overlays are closed
 */
export function unlockBodyScroll(): void {
  if (typeof document === 'undefined') return;

  scrollLockCount = Math.max(0, scrollLockCount - 1);

  if (scrollLockCount === 0) {
    const body = document.body;

    // Restore original values
    body.style.overflow = originalOverflow;
    body.style.paddingRight = originalPaddingRight;
  }
}

/**
 * Resets the scroll lock counter (useful for cleanup)
 */
export function resetScrollLock(): void {
  if (typeof document === 'undefined') return;

  scrollLockCount = 0;
  const body = document.body;
  body.style.overflow = originalOverflow;
  body.style.paddingRight = originalPaddingRight;
}

/**
 * Forcefully unlocks body scroll regardless of lock count
 * Useful for cleanup when you want to ensure scroll is always unlocked
 */
export function forceUnlockBodyScroll(): void {
  if (typeof document === 'undefined') return;

  scrollLockCount = 0;
  const body = document.body;
  body.style.overflow = originalOverflow || '';
  body.style.paddingRight = originalPaddingRight || '';
}
