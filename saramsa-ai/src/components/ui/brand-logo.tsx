'use client';

import Image from 'next/image';
import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';
import { cn } from './utils';

const LOGO_LIGHT = '/logo/Logo_black.svg';
const LOGO_DARK = '/logo/Logo_white.svg';

interface BrandLogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showText?: boolean;
}

export function BrandLogo({ className, size = 'md', showText = true }: BrandLogoProps) {
  const [mounted, setMounted] = useState(false);
  const { resolvedTheme } = useTheme();

  useEffect(() => {
    setMounted(true);
  }, []);

  const sizeClasses = {
    sm: 'h-6 w-auto',
    md: 'h-8 w-auto',
    lg: 'h-10 w-auto',
    xl: 'h-12 w-auto',
  };

  if (!mounted) {
    return (
      <div className={cn('flex items-center gap-3', className)}>
        <div className={cn(sizeClasses[size], 'bg-muted animate-pulse rounded')} />
        {showText && <div className="w-24 h-6 bg-muted animate-pulse rounded" />}
      </div>
    );
  }

  const logoSrc = resolvedTheme === 'dark' ? LOGO_DARK : LOGO_LIGHT;

  return (
    <div className={cn('flex items-center gap-3', className)}>
      <div className={cn('relative flex items-center', sizeClasses[size])}>
        <Image
          src={logoSrc}
          alt="Saramsa.ai"
          width={348}
          height={87}
          className="h-full w-auto max-w-[16rem] object-contain object-left"
          priority
          unoptimized
        />
      </div>
    </div>
  );
}
