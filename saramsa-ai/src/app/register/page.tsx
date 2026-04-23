'use client';

/*
 * Self-service registration is disabled while Saramsa AI is invite-only.
 * Visitors to /register are redirected to the invite-request form at /signup.
 *
 * The legacy register form is preserved in ./disabled-implementation.tsx
 * and can be restored by swapping that file's contents back into this file.
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function RegisterPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/signup');
  }, [router]);

  return null;
}
