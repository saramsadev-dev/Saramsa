import { getTokens, getValidAccessToken, refreshAccessToken, clearTokens } from './auth';

export interface AuthServiceConfig {
  refreshThresholdMs: number;
  maxRefreshAttempts: number; // Maximum refresh attempts before logout
}

const DEFAULT_CONFIG: AuthServiceConfig = {
  refreshThresholdMs: 5 * 60 * 1000, // 5 minutes
  maxRefreshAttempts: 3,
};

class AuthService {
  private config: AuthServiceConfig;
  private refreshAttempts: number = 0;
  private isRefreshing: boolean = false;
  private refreshPromise: Promise<string> | null = null;

  constructor(config: Partial<AuthServiceConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Get a valid access token, refreshing if necessary
   */
  async getValidToken(): Promise<string | null> {
    try {
      const token = getValidAccessToken();
      if (token) {
        // Check if token is expiring soon
        if (this.isTokenExpiringSoon(token)) {
          return await this.refreshTokenIfNeeded();
        }
        return token;
      }
      return null;
    } catch (error) {
      console.error('Error getting valid token:', error);
      return null;
    }
  }

  /**
   * Check if token will expire within the refresh threshold
   */
  private isTokenExpiringSoon(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Date.now() / 1000;
      const thresholdSeconds = this.config.refreshThresholdMs / 1000;
      return payload.exp && payload.exp < (currentTime + thresholdSeconds);
    } catch {
      return true;
    }
  }

  /**
   * Refresh token if needed, with proper error handling and retry logic
   */
  async refreshTokenIfNeeded(): Promise<string | null> {
    if (this.isRefreshing && this.refreshPromise) {
      // If already refreshing, wait for the existing promise
      try {
        return await this.refreshPromise;
      } catch (error) {
        console.error('Error waiting for token refresh:', error);
        return null;
      }
    }

    if (this.refreshAttempts >= this.config.maxRefreshAttempts) {
      console.error('Max refresh attempts reached, logging out');
      this.handleAuthFailure();
      return null;
    }

    try {
      this.isRefreshing = true;
      this.refreshAttempts++;
      
      this.refreshPromise = refreshAccessToken();
      const newToken = await this.refreshPromise;
      
      // Reset refresh attempts on success
      this.refreshAttempts = 0;
      return newToken;
      
    } catch (error) {
      console.error('Token refresh failed:', error);
      
      if (this.refreshAttempts >= this.config.maxRefreshAttempts) {
        this.handleAuthFailure();
      }
      
      return null;
    } finally {
      this.isRefreshing = false;
      this.refreshPromise = null;
    }
  }

  /**
   * Handle authentication failure by clearing tokens and redirecting to login
   */
  private handleAuthFailure(): void {
    clearTokens();
    
    // Redirect to login if not already there
    if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
  }

  /**
   * Reset refresh attempts (useful after successful login)
   */
  resetRefreshAttempts(): void {
    this.refreshAttempts = 0;
  }

  /**
   * Check if the service is currently refreshing a token
   */
  isCurrentlyRefreshing(): boolean {
    return this.isRefreshing;
  }

  /**
   * Get current refresh attempt count
   */
  getRefreshAttempts(): number {
    return this.refreshAttempts;
  }
}

// Export singleton instance
export const authService = new AuthService();

// Export the class for testing or custom instances
export { AuthService };
