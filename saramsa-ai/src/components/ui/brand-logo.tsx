'use client';

import Image from 'next/image';
import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';
import { cn } from './utils';

interface BrandLogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showText?: boolean;
}

export function BrandLogo({ className, size = 'md', showText = true }: BrandLogoProps) {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const sizeClasses = {
    sm: 'h-6 w-auto',
    md: 'h-8 w-auto',
    lg: 'h-10 w-auto',
    xl: 'h-12 w-auto'
  };

  if (!mounted) {
    return (
      <div className={cn('flex items-center gap-3', className)}>
        <div className={cn(sizeClasses[size], 'bg-muted animate-pulse rounded')} />
        {showText && <div className="w-24 h-6 bg-muted animate-pulse rounded" />}
      </div>
    );
  }

  const logoSrc = resolvedTheme === 'dark'
    ? 'https://res.cloudinary.com/do8i3k4ow/image/upload/v1757063313/saramsa-logo-dark_qzsgsm.png'
    : 'https://res.cloudinary.com/do8i3k4ow/image/upload/v1757063691/saramsa-logo-light_izly6v.png';

  return (
    <div className={cn('flex items-center gap-3', className)}>
      <div className={cn('relative', sizeClasses[size])}>
        <Image 
          src={logoSrc} 
          alt="Saramsa AI" 
          width={120}
          height={32}
          className="object-contain w-40 h-full" 
          priority 
        />
      </div>
      {/* {showText && (
        <span className={cn('font-bold text-foreground', textSizeClasses[size])}>
          Saramsa AI
        </span>
      )} */}
    </div>
  );
}


