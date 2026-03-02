
'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { loginUser, registerUser, setUser, logout as sliceLogout } from '@/store/features/auth/authSlice';
import { getStoredUser, getTokens, getCurrentUser, setStoredUser, logout as clientLogout, type User } from '@/lib/auth';
import { authService } from './authService';

type LoginArgs = { email: string; password: string };
type RegisterArgs = {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  otp: string;
  role?: 'admin' | 'user' | 'restricted user';
};

type HookResult = {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null | undefined;
  login: (args: LoginArgs) => Promise<{ success: true } | { success: false; error?: string }>;
  register: (
    args: RegisterArgs,
  ) => Promise<{ success: true } | { success: false; error?: string }>;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
};

export function useAuth(): HookResult {
  const dispatch = useAppDispatch();
  const auth = useAppSelector((s) => s.auth);
  const [hydrating, setHydrating] = useState(true);

  // On first mount (client only), hydrate auth state from localStorage tokens/user
  useEffect(() => {
    let cancelled = false;
    const hydrate = async () => {
      try {
        const tokens = getTokens();
        const storedUser = getStoredUser();
        
        if (storedUser && tokens) {
          // Check if we have valid tokens
          const validToken = await authService.getValidToken();
          if (validToken) {
            if (!cancelled) {
              setStoredUser(storedUser);
              dispatch(setUser(storedUser));
            }
          } else {
            // Tokens are invalid, clear them
            if (!cancelled) {
              clientLogout();
            }
          }
        } else if (tokens?.access) {
          try {
            const user = await getCurrentUser(tokens.access);
            if (!cancelled) {
              setStoredUser(user);
              dispatch(setUser(user));
            }
          } catch {
            // Token is invalid, ignore; user remains unauthenticated
            if (!cancelled) {
              clientLogout();
            }
          }
        }
      } finally {
        if (!cancelled) setHydrating(false);
      }
    };
    hydrate();
    return () => {
      cancelled = true;
    };
  }, [dispatch]);

  const login = useCallback<HookResult['login']>(async (args) => {
    try {
      await dispatch(loginUser(args)).unwrap();
      // Reset refresh attempts after successful login
      authService.resetRefreshAttempts();
      return { success: true };
    } catch (e: any) {
      return { success: false, error: e?.message || e || 'Login failed' };
    }
  }, [dispatch]);

  const register = useCallback<HookResult['register']>(async (args) => {
    try {
      await dispatch(registerUser(args)).unwrap();
      // Reset refresh attempts after successful registration
      authService.resetRefreshAttempts();
      return { success: true };
    } catch (e: any) {
      return { success: false, error: e?.message || e || 'Registration failed' };
    }
  }, [dispatch]);

  const logout = useCallback(async () => {
    try {
      // Clear client-side auth state
      clientLogout();
      // Clear Redux state
      dispatch(sliceLogout());
      // Force redirect to login page
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    } catch (error) {
      console.error('Logout error:', error);
      // Force redirect even if logout fails
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
  }, [dispatch]);

  const refreshToken = useCallback(async (): Promise<boolean> => {
    try {
      const newToken = await authService.refreshTokenIfNeeded();
      return !!newToken;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  }, []);

  return useMemo(() => ({
    user: auth.user,
    isAuthenticated: auth.isAuthenticated,
    loading: auth.loading || hydrating,
    error: auth.error,
    login,
    register,
    logout,
    refreshToken,
  }), [auth.user, auth.isAuthenticated, auth.loading, auth.error, hydrating, login, register, logout, refreshToken]);
}


