/**
 * Utility functions for handling authentication pages
 */

/**
 * Check if the current pathname is an authentication page
 * @param pathname - The current pathname
 * @returns true if the pathname is an auth page
 */
export function isAuthPage(pathname: string): boolean {
  return (
    pathname.startsWith("/login") ||
    pathname.startsWith("/register") ||
    pathname.startsWith("/forgot-password") ||
    pathname.startsWith("/reset-password")
  );
}

/**
 * Check if the current pathname should show the navbar
 * @param pathname - The current pathname
 * @param isAuthenticated - Whether the user is authenticated
 * @returns true if the navbar should be shown
 */
export function shouldShowNavbar(
  pathname: string,
  isAuthenticated: boolean
): boolean {
  // Don't show navbar on auth pages
  if (isAuthPage(pathname)) {
    return false;
  }

  // Don't show navbar on home page if not authenticated
  if (pathname === "/" && !isAuthenticated) {
    return false;
  }

  return true;
}
