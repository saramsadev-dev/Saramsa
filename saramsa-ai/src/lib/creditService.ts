/**
 * Credit API Service
 * Handles all credit-related API calls
 */

import { apiRequest } from './apiRequest';

export interface CreditBalance {
    balance: number;
    total_earned: number;
    total_spent: number;
}

export interface CreditTransaction {
    id: string;
    user_id: string;
    amount: number;
    transaction_type: 'debit' | 'credit';
    operation_type: string;
    metadata: Record<string, any>;
    created_at: string;
}

export interface CreditTransactionsResponse {
    transactions: CreditTransaction[];
    count: number;
    limit: number;
    offset: number;
}

export interface InsufficientCreditsError {
    type: string;
    title: string;
    status: number;
    detail: string;
    required: number;
    available: number;
    shortfall: number;
}

/**
 * Get current credit balance for authenticated user
 */
export const getCreditBalance = async (): Promise<CreditBalance> => {
    const response = await apiRequest('GET', '/auth/credits/balance/');
    // API returns: { success: true, data: { balance: 1000, ... } }
    // We need to return response.data.data to get the actual credit data
    return response.data.data;
};

/**
 * Get credit transaction history
 */
export const getCreditTransactions = async (
    limit: number = 50,
    offset: number = 0
): Promise<CreditTransactionsResponse> => {
    const response = await apiRequest('GET', `/auth/credits/transactions/?limit=${limit}&offset=${offset}`);
    return response.data;
};

/**
 * Admin: Add credits to a user
 */
export const adminAddCredits = async (
    userId: string,
    amount: number,
    reason: string = 'admin_grant'
): Promise<any> => {
    const response = await apiRequest('POST', '/auth/credits/admin/add/', {
        user_id: userId,
        amount,
        reason,
    });
    return response.data;
};

/**
 * Check if error is an insufficient credits error
 */
export const isInsufficientCreditsError = (error: any): boolean => {
    return error?.response?.status === 402 || error?.status === 402;
};

/**
 * Extract insufficient credits details from error
 */
export const getInsufficientCreditsDetails = (error: any): InsufficientCreditsError | null => {
    if (!isInsufficientCreditsError(error)) return null;

    const data = error?.response?.data || error?.data;
    return {
        type: data?.type || 'insufficient_credits',
        title: data?.title || 'Insufficient Credits',
        status: 402,
        detail: data?.detail || 'You do not have enough credits for this operation',
        required: data?.required || 0,
        available: data?.available || 0,
        shortfall: data?.shortfall || 0,
    };
};
