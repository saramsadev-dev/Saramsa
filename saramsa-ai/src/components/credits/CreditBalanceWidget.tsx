/**
 * Credit Balance Widget
 * Displays user's current credit balance with visual indicators
 */

'use client';

import React, { useEffect, useState } from 'react';
import { getCreditBalance, type CreditBalance } from '@/lib/creditService';
import { Coins, TrendingUp, TrendingDown } from 'lucide-react';

export function CreditBalanceWidget() {
    const [credits, setCredits] = useState<CreditBalance | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadCredits();
    }, []);

    const loadCredits = async () => {
        try {
            setLoading(true);
            const data = await getCreditBalance();
            setCredits(data);
            setError(null);
        } catch (err: any) {
            console.error('Failed to load credits:', err);
            setError('Failed to load credits');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center gap-2 px-4 py-2 bg-muted/50 rounded-lg animate-pulse">
                <Coins className="w-5 h-5 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Loading...</span>
            </div>
        );
    }

    if (error || !credits) {
        return (
            <div className="flex items-center gap-2 px-4 py-2 bg-destructive/10 rounded-lg">
                <Coins className="w-5 h-5 text-destructive" />
                <span className="text-sm text-destructive">Error loading credits</span>
            </div>
        );
    }

    const balanceColor =
        (credits?.balance ?? 0) > 500 ? 'text-green-600 dark:text-green-400' :
            (credits?.balance ?? 0) > 100 ? 'text-yellow-600 dark:text-yellow-400' :
                'text-red-600 dark:text-red-400';

    return (
        <div className="flex items-center gap-3 px-4 py-2 bg-card border rounded-lg shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-primary/10">
                <Coins className="w-5 h-5 text-primary" />
            </div>

            <div className="flex-1">
                <div className="flex items-baseline gap-2">
                    <span className={`text-2xl font-bold ${balanceColor}`}>
                        {(credits?.balance ?? 0).toLocaleString()}
                    </span>
                    <span className="text-xs text-muted-foreground">credits</span>
                </div>

                <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                        <TrendingUp className="w-3 h-3" />
                        <span>{(credits?.total_earned ?? 0).toLocaleString()} earned</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <TrendingDown className="w-3 h-3" />
                        <span>{(credits?.total_spent ?? 0).toLocaleString()} spent</span>
                    </div>
                </div>
                
                {/* Credit costs info */}
                <div className="mt-2 text-xs text-muted-foreground">
                    <p>• Analysis: 1 credit • User Story: 1 credit • Work Item: 1 credit</p>
                </div>
            </div>

            <button
                onClick={loadCredits}
                className="text-xs text-primary hover:underline"
                title="Refresh balance"
            >
                Refresh
            </button>
        </div>
    );
}

/**
 * Compact Credit Badge
 * Minimal credit display for navigation bars
 */
export function CreditBadge() {
    const [balance, setBalance] = useState<number | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadBalance = async () => {
            try {
                const data = await getCreditBalance();
                // Ensure we have a valid number
                const balanceValue = typeof data?.balance === 'number' ? data.balance : 0;
                setBalance(balanceValue);
            } catch (err) {
                console.error('Failed to load credit balance:', err);
                setBalance(0); // Set to 0 on error to show something
            } finally {
                setLoading(false);
            }
        };
        loadBalance();
    }, []);

    // Don't render anything while loading
    if (loading) {
        return (
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400">
                <Coins className="w-3.5 h-3.5" />
                <span>...</span>
            </div>
        );
    }

    // Ensure balance is a valid number before rendering
    const safeBalance = typeof balance === 'number' ? balance : 0;

    const badgeColor =
        safeBalance > 500 ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
            safeBalance > 100 ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' :
                'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';

    return (
        <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${badgeColor}`}>
            <Coins className="w-3.5 h-3.5" />
            <span>{safeBalance.toLocaleString()}</span>
        </div>
    );
}
