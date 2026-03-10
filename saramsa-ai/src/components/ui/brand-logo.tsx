'use client';

import Image from 'next/image';
import { useEffect, useState } from 'react';
import { cn } from './utils';

interface BrandLogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showText?: boolean;
}

export function BrandLogo({ className, size = 'md', showText = true }: BrandLogoProps) {
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

  const logoSrc = '/saramsa-logo-official.png';

  return (
    <div className={cn('flex items-center gap-3', className)}>
      <div className={cn('relative', sizeClasses[size])}>
        <Image 
          src={logoSrc} 
          alt="Saramsa.ai" 
          width={300}
          height={60}
          className="object-contain w-64 h-full"
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


