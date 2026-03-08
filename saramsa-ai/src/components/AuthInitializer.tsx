'use client';

import React, { useEffect, useState } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { setUser } from '@/store/features/auth/authSlice';
import { getStoredUser, getValidAccessToken, getTokens, clearTokens } from '@/lib/auth';

interface AuthInitializerProps {
  children: React.ReactNode;
}

export const AuthInitializer: React.FC<AuthInitializerProps> = ({ children }) => {
  const dispatch = useAppDispatch();
  useAppSelector((state) => state.auth);
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    // Initialize authentication state from localStorage
    const initializeAuth = async () => {
      
      try {
        const storedUser = getStoredUser();
        const tokens = getTokens();
        const validAccessToken = getValidAccessToken();

        if (storedUser && validAccessToken) {
          // User has valid tokens, restore authentication state
          dispatch(setUser(storedUser));
        } else if (tokens && !validAccessToken) {
          // User has tokens but access token is expired
          // The axios interceptor will handle token refresh automatically
          if (storedUser) {
            dispatch(setUser(storedUser));
          }
        } else {
          // Clear any invalid/corrupted data
          clearTokens();
        }
      } catch (error) {
        console.error('AuthInitializer: Error initializing authentication:', error);
        // Clear corrupted data
        clearTokens();
      } finally {
        setIsInitialized(true);
      }
    };

    initializeAuth();
  }, [dispatch]);

  // Show loading while initializing
  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-secondary/50 to-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-saramsa-brand mx-auto mb-4"></div>
          <p className="text-muted-foreground">Initializing authentication...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}; 
