'use client';

/*
 * /signup is a legacy URL from the invite-only era when this page hosted
 * a "request an invite" lead-capture form. Self-serve signup is back at
 * /register, so we redirect here. Any query params (notably ?invite=...)
 * are preserved so invite-link emails that point at /signup still land
 * the user on the real signup page.
 */

import { Suspense, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

function SignupRedirect() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const qs = searchParams?.toString();
    router.replace(qs ? `/register?${qs}` : '/register');
  }, [router, searchParams]);

  return null;
}

export default function SignupPage() {
  return (
    <Suspense fallback={null}>
      <SignupRedirect />
    </Suspense>
  );
}
