'use client';

import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/useAuth';
import { useEffect, useRef, useState } from 'react';

export default function HomePage() {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();
  const hasRedirectedRef = useRef(false);
  const [isRedirecting, setIsRedirecting] = useState(false);

  useEffect(() => {
    // Prevent multiple redirects
    if (hasRedirectedRef.current || isRedirecting) return;
    
    // Wait for auth to be determined
    if (loading) return;
    
    console.log("Redirecting based on auth:", isAuthenticated);
    
    hasRedirectedRef.current = true;
    setIsRedirecting(true);
    
    // Use setTimeout to prevent immediate redirect loops
    const timer = setTimeout(() => {
      if (isAuthenticated) {
        router.replace('/projects');
      } else {
        router.replace('/login');
      }
    }, 100);
    
    return () => clearTimeout(timer);
  }, [isAuthenticated, loading, router, isRedirecting]);

  // Show loading while checking auth or redirecting
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600 dark:text-gray-400">
          {loading ? 'Checking authentication...' : 'Redirecting...'}
        </p>
      </div>
    </div>
  );
}
