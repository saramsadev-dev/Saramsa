'use client';

import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/useAuth';
import { useEffect } from 'react';

export default function HomePage() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    console.log("isAuthenticated", isAuthenticated);
    
    // If authenticated, go to dashboard by default
    if (isAuthenticated) {
      router.push('/dashboard');
      return;
    }

    // If not authenticated, redirect to login
    router.push('/login');
  }, [isAuthenticated, router]);

  // Show loading while redirecting
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Redirecting...</p>
      </div>
    </div>
  );
}
