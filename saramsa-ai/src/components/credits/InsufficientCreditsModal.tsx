/**
 * Insufficient Credits Modal
 * Displays when user doesn't have enough credits for an operation
 */

'use client';

import React from 'react';
import { AlertCircle, Coins, X } from 'lucide-react';
import type { InsufficientCreditsError } from '@/lib/creditService';

interface InsufficientCreditsModalProps {
    error: InsufficientCreditsError;
    onClose: () => void;
    onViewCredits?: () => void;
}

export function InsufficientCreditsModal({
    error,
    onClose,
    onViewCredits
}: InsufficientCreditsModalProps) {
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="relative w-full max-w-md bg-card border rounded-lg shadow-2xl">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b">
                    <div className="flex items-center gap-3">
                        <div className="flex items-center justify-center w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30">
                            <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
                        </div>
                        <h2 className="text-lg font-semibold">Insufficient Credits</h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1 rounded-lg hover:bg-muted transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-4">
                    <p className="text-muted-foreground">
                        {error.detail}
                    </p>

                    {/* Credit Breakdown */}
                    <div className="grid grid-cols-3 gap-3 p-4 bg-muted/50 rounded-lg">
                        <div className="text-center">
                            <p className="text-xs text-muted-foreground mb-1">Required</p>
                            <p className="text-lg font-bold text-red-600 dark:text-red-400">
                                {error.required}
                            </p>
                        </div>
                        <div className="text-center">
                            <p className="text-xs text-muted-foreground mb-1">Available</p>
                            <p className="text-lg font-bold">
                                {error.available}
                            </p>
                        </div>
                        <div className="text-center">
                            <p className="text-xs text-muted-foreground mb-1">Shortfall</p>
                            <p className="text-lg font-bold text-orange-600 dark:text-orange-400">
                                {error.shortfall}
                            </p>
                        </div>
                    </div>

                    {/* Info Box */}
                    <div className="flex items-start gap-3 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                        <Coins className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" />
                        <div className="flex-1 text-sm">
                            <p className="font-medium text-blue-900 dark:text-blue-100 mb-1">
                                How to get more credits
                            </p>
                            <p className="text-blue-700 dark:text-blue-300">
                                Contact your administrator to request additional credits for your account.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Actions */}
                <div className="flex gap-3 p-6 border-t">
                    <button
                        onClick={onClose}
                        className="flex-1 px-4 py-2 border rounded-lg hover:bg-muted transition-colors"
                    >
                        Close
                    </button>
                    {onViewCredits && (
                        <button
                            onClick={() => {
                                onViewCredits();
                                onClose();
                            }}
                            className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
                        >
                            View Credits
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

/**
 * Hook to handle insufficient credits errors
 */
export function useInsufficientCreditsHandler() {
    const [error, setError] = React.useState<InsufficientCreditsError | null>(null);

    const handleError = (err: any) => {
        if (err?.response?.status === 402 || err?.status === 402) {
            const data = err?.response?.data || err?.data;
            setError({
                type: data?.type || 'insufficient_credits',
                title: data?.title || 'Insufficient Credits',
                status: 402,
                detail: data?.detail || 'You do not have enough credits',
                required: data?.required || 0,
                available: data?.available || 0,
                shortfall: data?.shortfall || 0,
            });
            return true;
        }
        return false;
    };

    const clearError = () => setError(null);

    return { error, handleError, clearError };
}
