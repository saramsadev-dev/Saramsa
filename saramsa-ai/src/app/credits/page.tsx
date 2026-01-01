/**
 * Credits Page
 * Full page view for managing credits and viewing transaction history
 */

'use client';

import React from 'react';
import { CreditBalanceWidget } from '@/components/credits/CreditBalanceWidget';
import { CreditTransactionHistory } from '@/components/credits/CreditTransactionHistory';
import { Coins, History, Info } from 'lucide-react';

export default function CreditsPage() {
    return (
        <div className="container max-w-4xl mx-auto p-6 space-y-6">
            {/* Header */}
            <div className="space-y-2">
                <h1 className="text-3xl font-bold flex items-center gap-3">
                    <Coins className="w-8 h-8 text-primary" />
                    Credits
                </h1>
                <p className="text-muted-foreground">
                    Manage your credits and view transaction history
                </p>
            </div>

            {/* Balance Section */}
            <div className="space-y-4">
                <h2 className="text-xl font-semibold">Current Balance</h2>
                <CreditBalanceWidget />
            </div>

            {/* Info Section */}
            <div className="flex items-start gap-3 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <Info className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" />
                <div className="flex-1 text-sm">
                    <p className="font-medium text-blue-900 dark:text-blue-100 mb-2">
                        About Credits
                    </p>
                    <ul className="space-y-1 text-blue-700 dark:text-blue-300">
                        <li>• <strong>Analysis Generation:</strong> 50 credits per analysis</li>
                        <li>• <strong>User Story Creation:</strong> 30 credits per story</li>
                        <li>• <strong>Work Item Creation:</strong> 20 credits per item</li>
                    </ul>
                    <p className="mt-3 text-blue-700 dark:text-blue-300">
                        Need more credits? Contact your administrator.
                    </p>
                </div>
            </div>

            {/* Transaction History */}
            <div className="space-y-4">
                <h2 className="text-xl font-semibold flex items-center gap-2">
                    <History className="w-5 h-5" />
                    Transaction History
                </h2>
                <div className="bg-card border rounded-lg p-6">
                    <CreditTransactionHistory />
                </div>
            </div>
        </div>
    );
}
