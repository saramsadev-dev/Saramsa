'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Mail, ArrowRight, ArrowLeft } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import dynamic from 'next/dynamic';
import { apiRequest } from '@/lib/apiRequest';
import { DataStream, TaskCards, AIProcessing } from '@/components/ui/animations';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

// Lazy-load components to avoid SSR issues
const ThemeToggle = dynamic(
  () => import('@/components/ui/theme-toggle').then(mod => mod.ThemeToggle),
  { ssr: false }
);

const BrandLogo = dynamic(
  () => import('@/components/ui/brand-logo').then(mod => mod.BrandLogo),
  { ssr: false }
);

// Form validation schema
const forgotPasswordSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
});

type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;

export default function ForgotPasswordPage() {
  const [mounted, setMounted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [resetLink, setResetLink] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const onSubmit = async (data: ForgotPasswordFormData) => {
    setIsLoading(true);
    setError(null);
    setSuccess(false);
    setResetLink(null);
    
    try {
      const result = await apiRequest(
        'post',
        '/auth/forgot-password/',
        { email: data.email },
        false // No auth required for forgot password
      );
      
      if (result.data?.success || result.status === 200) {
        setSuccess(true);
        // In development, log the reset link if provided
        if (result.data?.reset_link) {
          setResetLink(result.data.reset_link);
        }
      } else {
        setError(result.data?.error || 'Failed to send reset email. Please try again.');
      }
    } catch (error: any) {
      console.error('Forgot password error:', error);
      setError(error.response?.data?.error || error.response?.data?.message || 'Failed to send reset email. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (!mounted) return null;

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-background text-foreground transition-colors duration-300 relative">
      {/* Theme toggle button */}
      <div className="fixed top-3 right-3 sm:top-4 sm:right-4 md:top-6 md:right-6 z-50">
        <ThemeToggle />
      </div>

      {/* Left Visual Pane - Hidden on mobile, visible on tablet+ */}
      <div className="hidden md:flex md:w-full lg:w-1/2 xl:w-1/2 2xl:w-1/2 relative bg-gradient-to-br from-background via-secondary/80 to-saramsa-brand/20 dark:from-background dark:via-muted/60 dark:to-accent/40 overflow-hidden min-h-[40vh] lg:min-h-screen">
        <div className="absolute inset-0 bg-gradient-to-br from-saramsa-brand/15 via-transparent to-saramsa-gradient-to/15 dark:from-saramsa-brand/10 dark:to-saramsa-gradient-to/10" />
        
        {/* Data Stream Animation - Hidden on tablet/iPad */}
        {/* <div className="hidden lg:block">
          <DataStream />
        </div> */}
        
        {/* Floating Task Cards - Hidden on tablet/iPad */}
        <div className="hidden lg:block">
          <TaskCards variant="login" />
        </div>
        
        <div className="relative z-10 flex flex-col justify-center px-6 md:px-8 lg:px-12 py-8 lg:py-0">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.5 }}
            className="max-w-full mx-auto lg:mx-0"
          >
            <h1 className="text-2xl md:text-3xl lg:text-4xl xl:text-2xl 2xl:text-4xl font-semibold mb-4 md:mb-6 text-foreground leading-tight">
              Transform Feedback into Action
            </h1>
            <p className="text-sm md:text-base lg:text-lg xl:text-sm 2xl:text-lg text-muted-foreground mb-6 md:mb-8 leading-relaxed">
              Saramsa AI processes customer feedback and automatically identifies actionable insights,
              giving product teams the insights to build better products.
            </p>
            <div className="space-y-3 md:space-y-4">
              {[
                'AI-powered feedback analysis',
                'Automated Jira task creation',
                'Smart priority recommendations',
              ].map((feature, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.8, delay: 1 + index * 0.2 }}
                  className="flex items-center gap-3"
                >
                  <div className="w-2 h-2 bg-saramsa-brand rounded-full animate-pulse-glow shadow-[0_0_16px_rgba(139,95,191,0.45)] flex-shrink-0" />
                  <span className="text-sm md:text-base xl:text-xs text-muted-foreground">{feature}</span>
                </motion.div>
              ))}
            </div>
            
            {/* AI Processing Animation - Hidden on tablet/iPad */}
            <div className="hidden lg:block">
              <AIProcessing />
            </div>
          </motion.div>
        </div>
      </div>

      {/* Right Forgot Password Form */}
      <div className="w-full md:w-full lg:w-1/2 xl:w-1/2 2xl:w-1/2 flex items-center justify-center p-4 sm:p-6 md:p-8 lg:p-8 xl:p-12 bg-card md:border-l border-border dark:border-border/60 dark:bg-card/70 relative overflow-y-auto min-h-screen md:min-h-[60vh] lg:min-h-screen">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8 }}
          className="w-full max-w-md mx-auto space-y-6 sm:space-y-8"
        >
          {/* Logo */}
          <div className="text-center">
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="mb-6 sm:mb-8"
            >
              <BrandLogo size="lg" className="justify-center" />
            </motion.div>
          </div>

          {/* Header */}
          <div className="text-center">
            <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-3xl xl:text-2xl 2xl:text-3xl font-semibold text-foreground mb-2 sm:mb-3">
              Forgot Password?
            </h2>
            <p className="mt-2 sm:mt-3 text-sm sm:text-base md:text-lg lg:text-base xl:text-xs 2xl:text-base text-muted-foreground leading-relaxed px-2 sm:px-0">
              {success 
                ? 'We\'ve sent you a password reset link. Please check your email.'
                : 'Enter your email address and we\'ll send you a link to reset your password.'
              }
            </p>
          </div>

          {/* Success Message */}
          {success && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-secondary border border-border rounded-2xl p-4 dark:bg-secondary/60 dark:border-border/60"
            >
              <p className="text-sm text-muted-foreground">
                If an account exists with this email, you will receive a password reset link shortly.
              </p>
              {resetLink && process.env.NODE_ENV === 'development' && (
                <div className="mt-3 space-y-2">
                  <p className="text-xs text-muted-foreground">
                    Development link:
                  </p>
                  <div className="flex flex-col sm:flex-row gap-2">
                    <Input
                      value={resetLink}
                      readOnly
                      className="text-xs"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      className="text-xs"
                      onClick={() => {
                        if (typeof window !== 'undefined') {
                          window.open(resetLink, '_blank', 'noopener,noreferrer');
                        }
                      }}
                    >
                      Open Link
                    </Button>
                  </div>
                </div>
              )}
            </motion.div>
          )}

          {/* Error Message */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-secondary border border-border rounded-2xl p-4 dark:bg-secondary/60 dark:border-border/60"
            >
              <p className="text-sm text-muted-foreground">{error}</p>
            </motion.div>
          )}

          {/* Form */}
          {!success && (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 sm:space-y-6">
              <div className="space-y-3 sm:space-y-4">
                {/* Email */}
                <div>
                  <label htmlFor="email" className="block text-xs sm:text-sm md:text-base lg:text-sm xl:text-xs 2xl:text-sm font-medium text-foreground mb-1 sm:mb-2">
                    Email Address
                  </label>
                  <div className="relative mt-1 sm:mt-2">
                    <Input
                      {...register('email')}
                      id="email"
                      type="email"
                      placeholder="Enter your email address"
                      className="w-full pl-8 sm:pl-10 pr-3 py-2.5 sm:py-3 text-sm sm:text-sm md:text-sm lg:text-sm xl:text-sm 2xl:text-sm bg-background border border-border rounded-2xl focus:border-saramsa-brand/50 focus:ring-2 focus:ring-saramsa-brand/20 focus:outline-none transition-all duration-300 text-foreground placeholder:text-muted-foreground shadow-[inset_0_1px_2px_rgba(0,0,0,0.06)] dark:bg-background/80 dark:border-border/60 dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.4)]"
                    />
                    <Mail className="absolute left-2.5 sm:left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 sm:w-4 sm:h-4 text-muted-foreground" />
                  </div>
                  {errors.email && (
                    <p className="mt-1 text-xs sm:text-sm text-red-500">{errors.email.message}</p>
                  )}
                </div>
              </div>

              {/* Submit Button */}
              <Button
                type="submit"
                disabled={isLoading}
                variant="saramsa"
                className="w-full py-2.5 sm:py-3 text-sm sm:text-base md:text-lg lg:text-base xl:text-xs 2xl:text-base group"
              >
                {isLoading ? (
                  <div className="w-4 h-4 sm:w-5 sm:h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mx-auto" />
                ) : (
                  <>
                    Send Reset Link
                    <ArrowRight className="ml-2 w-3.5 h-3.5 sm:w-4 sm:h-4 group-hover:translate-x-1 transition-transform inline" />
                  </>
                )}
              </Button>
            </form>
          )}

          {/* Back to Login Link */}
          <div className="text-center">
            <Link
              href="/login"
              className="inline-flex items-center text-xs sm:text-sm md:text-base lg:text-sm xl:text-xs 2xl:text-sm text-saramsa-brand hover:text-saramsa-brand-hover font-medium transition-colors group"
            >
              <ArrowLeft className="mr-2 w-3.5 h-3.5 sm:w-4 sm:h-4 group-hover:-translate-x-1 transition-transform" />
              Back to Login
            </Link>
          </div>

          {/* Register Link */}
          <div className="text-center">
            <p className="text-xs sm:text-sm md:text-base lg:text-sm xl:text-xs 2xl:text-sm text-muted-foreground">
              Don't have an account?{' '}
              <Link
                href="/register"
                className="text-saramsa-brand hover:text-saramsa-brand-hover font-medium transition-colors"
              >
                Create an account
              </Link>
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
}



