/**
 * Credit Transaction History Component
 * Displays paginated list of credit transactions
 */

'use client';

import React, { useEffect, useState } from 'react';
import { getCreditTransactions, type CreditTransaction } from '@/lib/creditService';
import { ArrowDownCircle, ArrowUpCircle, Clock, ChevronLeft, ChevronRight } from 'lucide-react';

export function CreditTransactionHistory() {
    const [transactions, setTransactions] = useState<CreditTransaction[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [page, setPage] = useState(0);
    const [hasMore, setHasMore] = useState(true);
    const limit = 20;

    useEffect(() => {
        loadTransactions();
    }, [page]);

    const loadTransactions = async () => {
        try {
            setLoading(true);
            const data = await getCreditTransactions(limit, page * limit);
            
            // Safely handle the response structure
            const transactionList = Array.isArray(data?.transactions) ? data.transactions : [];
            const count = typeof data?.count === 'number' ? data.count : 0;
            
            setTransactions(transactionList);
            setHasMore(count === limit);
            setError(null);
        } catch (err: any) {
            console.error('Failed to load transactions:', err);
            setError('Failed to load transaction history');
            setTransactions([]); // Set empty array on error
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        }).format(date);
    };

    const getOperationLabel = (type: string) => {
        const labels: Record<string, string> = {
            analysis: 'Analysis Generation',
            user_story: 'User Story Creation',
            work_item: 'Work Item Creation',
            admin_grant: 'Admin Grant',
            top_up: 'Credit Purchase',
            initial_credits: 'Welcome Bonus',
        };
        return labels[type] || type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    };

    if (loading && (transactions?.length ?? 0) === 0) {
        return (
            <div className="space-y-3">
                {[...Array(5)].map((_, i) => (
                    <div key={i} className="flex items-center gap-3 p-4 bg-muted/50 rounded-lg animate-pulse">
                        <div className="w-10 h-10 bg-muted rounded-full" />
                        <div className="flex-1 space-y-2">
                            <div className="h-4 bg-muted rounded w-1/3" />
                            <div className="h-3 bg-muted rounded w-1/4" />
                        </div>
                        <div className="h-6 bg-muted rounded w-16" />
                    </div>
                ))}
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-8 text-center">
                <p className="text-destructive">{error}</p>
                <button
                    onClick={loadTransactions}
                    className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
                >
                    Retry
                </button>
            </div>
        );
    }

    if ((transactions?.length ?? 0) === 0) {
        return (
            <div className="p-8 text-center text-muted-foreground">
                <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No transactions yet</p>
                <p className="text-sm mt-1">Your credit activity will appear here</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* Transaction List */}
            <div className="space-y-2">
                {(transactions ?? []).map((transaction) => {
                    const isDebit = transaction.transaction_type === 'debit';

                    return (
                        <div
                            key={transaction.id}
                            className="flex items-center gap-3 p-4 bg-card border rounded-lg hover:shadow-sm transition-shadow"
                        >
                            {/* Icon */}
                            <div className={`flex items-center justify-center w-10 h-10 rounded-full ${isDebit
                                    ? 'bg-red-100 dark:bg-red-900/30'
                                    : 'bg-green-100 dark:bg-green-900/30'
                                }`}>
                                {isDebit ? (
                                    <ArrowDownCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
                                ) : (
                                    <ArrowUpCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                                )}
                            </div>

                            {/* Details */}
                            <div className="flex-1 min-w-0">
                                <p className="font-medium text-sm truncate">
                                    {getOperationLabel(transaction.operation_type)}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                    {formatDate(transaction.created_at)}
                                </p>
                            </div>

                            {/* Amount */}
                            <div className={`text-right ${isDebit
                                    ? 'text-red-600 dark:text-red-400'
                                    : 'text-green-600 dark:text-green-400'
                                }`}>
                                <p className="font-bold text-lg">
                                    {isDebit ? '-' : '+'}{transaction.amount}
                                </p>
                                <p className="text-xs opacity-75">credits</p>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between pt-4 border-t">
                <button
                    onClick={() => setPage(p => Math.max(0, p - 1))}
                    disabled={page === 0}
                    className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border disabled:opacity-50 disabled:cursor-not-allowed hover:bg-muted"
                >
                    <ChevronLeft className="w-4 h-4" />
                    Previous
                </button>

                <span className="text-sm text-muted-foreground">
                    Page {page + 1}
                </span>

                <button
                    onClick={() => setPage(p => p + 1)}
                    disabled={!hasMore}
                    className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border disabled:opacity-50 disabled:cursor-not-allowed hover:bg-muted"
                >
                    Next
                    <ChevronRight className="w-4 h-4" />
                </button>
            </div>
        </div>
    );
}
