/**
 * Billing Service
 * Handles Stripe subscription and billing portal integration
 */

import { apiRequest } from './apiRequest';

export interface SubscriptionStatus {
  is_subscribed: boolean;
  subscription_status?:
    | 'active'
    | 'trialing'
    | 'past_due'
    | 'canceled'
    | 'incomplete'
    | 'incomplete_expired'
    | 'unpaid'
    | 'inactive';
  plan_name?: string;
  current_period_end?: string;
  cancel_at_period_end?: boolean;
  customer_id?: string;
}

function mapSubscriptionPayload(data: Record<string, unknown>): SubscriptionStatus {
  const statusRaw = data.subscription_status ?? data.status;
  const status =
    typeof statusRaw === 'string'
      ? (statusRaw.toLowerCase() as SubscriptionStatus['subscription_status'])
      : undefined;
  const isSubscribed =
    Boolean(data.is_subscribed) ||
    Boolean(data.has_subscription) ||
    Boolean(data.is_active);

  return {
    is_subscribed: isSubscribed,
    subscription_status: status,
    plan_name: typeof data.plan_name === 'string' ? data.plan_name : undefined,
    current_period_end:
      typeof data.current_period_end === 'string' ? data.current_period_end : undefined,
    cancel_at_period_end:
      typeof data.cancel_at_period_end === 'boolean' ? data.cancel_at_period_end : undefined,
    customer_id:
      (typeof data.customer_id === 'string' ? data.customer_id : undefined) ??
      (typeof data.stripe_customer_id === 'string' ? data.stripe_customer_id : undefined),
  };
}

/**
 * Get the current user's Stripe subscription status
 */
export async function getStripeSubscriptionStatus(): Promise<SubscriptionStatus> {
  try {
    const response = await apiRequest('get', '/billing/stripe/subscription/', undefined, true);
    const data = (response.data?.data || response.data || {}) as Record<string, unknown>;

    return mapSubscriptionPayload(data);
  } catch (error: any) {
    console.error('Failed to fetch subscription status:', error);
    throw new Error(error?.message || 'Failed to load subscription status');
  }
}

/**
 * Create a Stripe Checkout session to start a new subscription
 */
export async function createStripeCheckoutSession(): Promise<{ checkout_url: string }> {
  try {
    const response = await apiRequest('post', '/billing/stripe/checkout-session/', {}, true);
    const data = response.data?.data || response.data || {};

    if (!data.checkout_url) {
      throw new Error('No checkout URL returned from server');
    }

    return {
      checkout_url: data.checkout_url,
    };
  } catch (error: any) {
    console.error('Failed to create checkout session:', error);
    throw new Error(error?.message || 'Failed to start checkout');
  }
}

/**
 * Create a Stripe Billing Portal session to manage subscription
 */
export async function createStripeBillingPortalSession(): Promise<{ portal_url: string }> {
  try {
    const response = await apiRequest('post', '/billing/stripe/portal-session/', {}, true);
    const data = response.data?.data || response.data || {};

    if (!data.portal_url) {
      throw new Error('No portal URL returned from server');
    }

    return {
      portal_url: data.portal_url,
    };
  } catch (error: any) {
    console.error('Failed to create billing portal session:', error);
    throw new Error(error?.message || 'Failed to open billing portal');
  }
}

/**
 * Cancel subscription at the end of the current billing period
 */
export async function cancelSubscription(): Promise<{ success: boolean; message?: string }> {
  try {
    const response = await apiRequest('post', '/billing/cancel-subscription/', {}, true);
    const data = response.data?.data || response.data || {};

    return {
      success: true,
      message: data.message || 'Subscription canceled successfully',
    };
  } catch (error: any) {
    console.error('Failed to cancel subscription:', error);
    throw new Error(error?.message || 'Failed to cancel subscription');
  }
}

/**
 * Resume a canceled subscription
 */
export async function resumeSubscription(): Promise<{ success: boolean; message?: string }> {
  try {
    const response = await apiRequest('post', '/billing/resume-subscription/', {}, true);
    const data = response.data?.data || response.data || {};

    return {
      success: true,
      message: data.message || 'Subscription resumed successfully',
    };
  } catch (error: any) {
    console.error('Failed to resume subscription:', error);
    throw new Error(error?.message || 'Failed to resume subscription');
  }
}
