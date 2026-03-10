'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Clock, CheckCircle, XCircle, AlertCircle, Loader2 } from 'lucide-react';

interface StatusDurationDisplayProps {
  status: 'success' | 'failure' | 'processing' | 'pending' | 'warning';
  duration?: string;
  title: string;
  description?: string;
  showIcon?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function StatusDurationDisplay({ 
  status, 
  duration, 
  title, 
  description, 
  showIcon = true,
  size = 'md'
}: StatusDurationDisplayProps) {
  
  const getStatusConfig = () => {
    switch (status) {
      case 'success':
        return {
          icon: CheckCircle,
          bgColor: 'bg-gradient-to-r from-green-100 to-emerald-100 dark:from-green-900/30 dark:to-emerald-900/30',
          borderColor: 'border-green-300 dark:border-green-600',
          textColor: 'text-green-800 dark:text-green-300',
          iconColor: 'text-green-600 dark:text-green-400',
          durationBg: 'bg-green-200 dark:bg-green-800/50',
          emoji: '✅'
        };
      case 'failure':
        return {
          icon: XCircle,
          bgColor: 'bg-gradient-to-r from-red-100 to-rose-100 dark:from-red-900/30 dark:to-rose-900/30',
          borderColor: 'border-red-300 dark:border-red-600',
          textColor: 'text-red-800 dark:text-red-300',
          iconColor: 'text-red-600 dark:text-red-400',
          durationBg: 'bg-red-200 dark:bg-red-800/50',
          emoji: '❌'
        };
      case 'processing':
        return {
          icon: Loader2,
          bgColor: 'bg-gradient-to-r from-saramsa-brand/10 to-saramsa-gradient-to/10 dark:from-saramsa-brand/20 dark:to-saramsa-gradient-to/20',
          borderColor: 'border-saramsa-brand/30 dark:border-saramsa-brand/40',
          textColor: 'text-saramsa-brand dark:text-saramsa-brand',
          iconColor: 'text-saramsa-brand dark:text-saramsa-brand',
          durationBg: 'bg-saramsa-brand/10 dark:bg-saramsa-brand/20',
          emoji: '⚙️'
        };
      case 'pending':
        return {
          icon: AlertCircle,
          bgColor: 'bg-gradient-to-r from-saramsa-brand/10 to-saramsa-gradient-to/10 dark:from-saramsa-brand/20 dark:to-saramsa-gradient-to/20',
          borderColor: 'border-saramsa-brand/30 dark:border-saramsa-brand/40',
          textColor: 'text-saramsa-brand dark:text-saramsa-brand',
          iconColor: 'text-saramsa-brand dark:text-saramsa-brand',
          durationBg: 'bg-saramsa-brand/10 dark:bg-saramsa-brand/20',
          emoji: '⏳'
        };
      case 'warning':
        return {
          icon: AlertCircle,
          bgColor: 'bg-gradient-to-r from-orange-100 to-yellow-100 dark:from-orange-900/30 dark:to-yellow-900/30',
          borderColor: 'border-orange-300 dark:border-orange-600',
          textColor: 'text-orange-800 dark:text-orange-300',
          iconColor: 'text-orange-600 dark:text-orange-400',
          durationBg: 'bg-orange-200 dark:bg-orange-800/50',
          emoji: '⚠️'
        };
      default:
        return {
          icon: AlertCircle,
          bgColor: 'bg-gradient-to-r from-secondary/40 to-secondary/20 dark:from-secondary/40 dark:to-secondary/30',
          borderColor: 'border-border/60 dark:border-border/60',
          textColor: 'text-foreground dark:text-muted-foreground',
          iconColor: 'text-muted-foreground dark:text-muted-foreground',
          durationBg: 'bg-secondary/60 dark:bg-card/50',
          emoji: 'ℹ️'
        };
    }
  };

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return {
          container: 'p-3',
          title: 'text-sm font-medium',
          description: 'text-xs',
          icon: 'w-4 h-4',
          duration: 'text-xs px-2 py-1'
        };
      case 'lg':
        return {
          container: 'p-6',
          title: 'text-lg font-semibold',
          description: 'text-sm',
          icon: 'w-6 h-6',
          duration: 'text-sm px-3 py-2'
        };
      default: // md
        return {
          container: 'p-4',
          title: 'text-base font-medium',
          description: 'text-sm',
          icon: 'w-5 h-5',
          duration: 'text-xs px-2 py-1'
        };
    }
  };

  const config = getStatusConfig();
  const sizeClasses = getSizeClasses();
  const IconComponent = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className={`
        ${config.bgColor} 
        ${config.borderColor} 
        ${sizeClasses.container}
        border-2 rounded-xl shadow-sm hover:shadow-md transition-all duration-300
      `}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {showIcon && (
            <div className="flex items-center gap-2">
              <span className="text-lg">{config.emoji}</span>
              <IconComponent 
                className={`${sizeClasses.icon} ${config.iconColor} ${status === 'processing' ? 'animate-spin' : ''}`} 
              />
            </div>
          )}
          
          <div>
            <h3 className={`${sizeClasses.title} ${config.textColor}`}>
              {title}
            </h3>
            {description && (
              <p className={`${sizeClasses.description} text-muted-foreground dark:text-muted-foreground mt-1`}>
                {description}
              </p>
            )}
          </div>
        </div>

        {duration && (
          <div className="flex items-center gap-2">
            <Clock className="w-3 h-3 text-muted-foreground dark:text-muted-foreground" />
            <span className={`
              ${sizeClasses.duration} 
              ${config.durationBg} 
              ${config.textColor}
              font-mono font-medium rounded-full
            `}>
              {duration}
            </span>
          </div>
        )}
      </div>
    </motion.div>
  );
}

// Example usage component for demonstration
export function StatusDurationExamples() {
  return (
    <div className="space-y-4 p-6">
      <h2 className="text-xl font-bold text-foreground dark:text-foreground mb-4">
        Colorful Status & Duration Display Examples
      </h2>
      
      <div className="grid gap-4">
        <StatusDurationDisplay
          status="success"
          title="Analysis Complete"
          description="Successfully processed 1,234 comments"
          duration="2.3s"
        />
        
        <StatusDurationDisplay
          status="failure"
          title="Upload Failed"
          description="Could not process the uploaded file"
          duration="0.8s"
        />
        
        <StatusDurationDisplay
          status="processing"
          title="Analyzing Comments"
          description="Processing feedback data with AI..."
          duration="45s"
        />
        
        <StatusDurationDisplay
          status="pending"
          title="Waiting for Input"
          description="Select a file to begin analysis"
        />
        
        <StatusDurationDisplay
          status="warning"
          title="Partial Success"
          description="Some items could not be processed"
          duration="1.2s"
        />
      </div>

      <div className="mt-6">
        <h3 className="text-lg font-semibold text-foreground dark:text-foreground mb-3">
          Different Sizes
        </h3>
        <div className="space-y-3">
          <StatusDurationDisplay
            status="success"
            title="Small Success"
            duration="0.5s"
            size="sm"
          />
          
          <StatusDurationDisplay
            status="processing"
            title="Medium Processing"
            description="Standard size display"
            duration="12s"
            size="md"
          />
          
          <StatusDurationDisplay
            status="failure"
            title="Large Failure Display"
            description="This is a larger display with more prominent styling"
            duration="3.7s"
            size="lg"
          />
        </div>
      </div>
    </div>
  );
}



