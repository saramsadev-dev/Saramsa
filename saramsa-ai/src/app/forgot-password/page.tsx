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

  // Handle component mount
  useEffect(() => {
    setMounted(true);
    
    // Cleanup function
    return () => {
      // Any cleanup code if needed
    };
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
        if (result.data?.reset_link && typeof window !== 'undefined') {
          console.log('Reset link:', result.data.reset_link);
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
      <div className="hidden md:flex md:w-full lg:w-1/2 xl:w-1/2 2xl:w-1/2 relative bg-gradient-to-br from-background via-muted/50 to-accent overflow-hidden min-h-[40vh] lg:min-h-screen">
        <div className="absolute inset-0 bg-gradient-to-br from-saramsa-brand/5 via-transparent to-saramsa-gradient-to/5" />
        
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
            <h1 className="text-2xl md:text-3xl lg:text-4xl xl:text-2xl 2xl:text-4xl font-bold mb-4 md:mb-6 text-foreground leading-tight">
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
                  <div className="w-2 h-2 bg-saramsa-brand rounded-full animate-pulse-glow shadow-lg flex-shrink-0" />
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
      <div className="w-full md:w-full lg:w-1/2 xl:w-1/2 2xl:w-1/2 flex items-center justify-center p-4 sm:p-6 md:p-8 lg:p-8 xl:p-12 bg-card md:border-l border-border relative overflow-y-auto min-h-screen md:min-h-[60vh] lg:min-h-screen">
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
            <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-3xl xl:text-2xl 2xl:text-3xl font-bold text-foreground mb-2 sm:mb-3">
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
              className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4"
            >
              <p className="text-sm text-green-600 dark:text-green-400">
                If an account exists with this email, you will receive a password reset link shortly.
              </p>
            </motion.div>
          )}

          {/* Error Message */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4"
            >
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </motion.div>
          )}

          {/* Form */}
          {!success && (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 sm:space-y-6">
              <div className="space-y-3 sm:space-y-4">
                {/* Email */}
                <div>
                  <label htmlFor="email" className="block text-xs sm:text-sm md:text-base lg:text-sm xl:text-xs 2xl:text-sm font-medium text-gray-900 dark:text-white mb-1 sm:mb-2">
                    Email Address
                  </label>
                  <div className="relative mt-1 sm:mt-2">
                    <input
                      {...register('email')}
                      id="email"
                      type="email"
                      placeholder="Enter your email address"
                      className="w-full pl-8 sm:pl-10 pr-3 py-2.5 sm:py-3 text-sm sm:text-sm md:text-sm lg:text-sm xl:text-sm 2xl:text-sm bg-gray-50 dark:bg-gray-800 border border-gray-200 
                      dark:border-gray-700 rounded-lg focus:border-[#E603EB] focus:ring-[#E603EB]/20 focus:outline-none transition-all duration-300 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                    />
                    <Mail className="absolute left-2.5 sm:left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 sm:w-4 sm:h-4 text-gray-400" />
                  </div>
                  {errors.email && (
                    <p className="mt-1 text-xs sm:text-sm text-red-500">{errors.email.message}</p>
                  )}
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-gradient-to-r from-saramsa-brand to-saramsa-gradient-to hover:from-saramsa-brand-hover hover:to-saramsa-gradient-to text-white py-2.5 sm:py-3 px-4 rounded-lg text-sm sm:text-base md:text-lg lg:text-base xl:text-xs 2xl:text-base font-medium shadow-lg hover:shadow-xl transition-all duration-300 group disabled:opacity-50 disabled:cursor-not-allowed animate-glow"
              >
                {isLoading ? (
                  <div className="w-4 h-4 sm:w-5 sm:h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mx-auto" />
                ) : (
                  <>
                    Send Reset Link
                    <ArrowRight className="ml-2 w-3.5 h-3.5 sm:w-4 sm:h-4 group-hover:translate-x-1 transition-transform inline" />
                  </>
                )}
              </button>
            </form>
          )}

          {/* Back to Login Link */}
          <div className="text-center">
            <Link
              href="/login"
              className="inline-flex items-center text-xs sm:text-sm md:text-base lg:text-sm xl:text-xs 2xl:text-sm text-[#E603EB] hover:text-[#E603EB]/80 font-medium transition-colors group"
            >
              <ArrowLeft className="mr-2 w-3.5 h-3.5 sm:w-4 sm:h-4 group-hover:-translate-x-1 transition-transform" />
              Back to Login
            </Link>
          </div>

          {/* Register Link */}
          <div className="text-center">
            <p className="text-xs sm:text-sm md:text-base lg:text-sm xl:text-xs 2xl:text-sm text-gray-600 dark:text-gray-400">
              Don't have an account?{' '}
              <Link
                href="/register"
                className="text-[#E603EB] hover:text-[#E603EB]/80 font-medium transition-colors"
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

