'use client';

import { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams, useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Lock, Eye, EyeOff, ArrowRight, ArrowLeft, CheckCircle } from 'lucide-react';
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
const resetPasswordSchema = z.object({
  new_password: z.string().min(6, 'Password must be at least 6 characters'),
  confirm_password: z.string().min(6, 'Please confirm your password'),
}).refine((data) => data.new_password === data.confirm_password, {
  message: "Passwords don't match",
  path: ["confirm_password"],
});

type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

function ResetPasswordContent() {
  const [mounted, setMounted] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const searchParams = useSearchParams();
  const router = useRouter();

  // Handle component mount
  useEffect(() => {
    setMounted(true);
    
    // Get token from URL
    const tokenParam = searchParams.get('token');
    if (tokenParam) {
      setToken(tokenParam);
    } else {
      setError('Invalid reset link. Please request a new password reset.');
    }
  }, [searchParams]);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
  });

  const onSubmit = async (data: ResetPasswordFormData) => {
    if (!token) {
      setError('Invalid reset link. Please request a new password reset.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccess(false);
    
    try {
      const result = await apiRequest(
        'post',
        '/auth/reset-password/',
        {
          token: token,
          new_password: data.new_password,
          confirm_password: data.confirm_password,
        },
        false // No auth required for reset password
      );
      
      if (result.data?.success || result.status === 200) {
        setSuccess(true);
        // Redirect to login after 2 seconds
        setTimeout(() => {
          router.push('/login');
        }, 2000);
      } else {
        setError(result.data?.error || 'Failed to reset password. Please try again.');
      }
    } catch (error: any) {
      console.error('Reset password error:', error);
      setError(error.response?.data?.error || error.response?.data?.message || 'Failed to reset password. Please try again.');
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

      {/* Right Reset Password Form */}
      <div className="w-full md:w-full lg:w-1/2 xl:w-1/2 2xl:w-1/2 flex items-center justify-center p-4 sm:p-6 md:p-8 lg:p-8 xl:p-12 bg-card md:border-l border-border/60 dark:bg-card/70 relative overflow-y-auto min-h-screen md:min-h-[60vh] lg:min-h-screen">
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
              Reset Password
            </h2>
            <p className="mt-2 sm:mt-3 text-sm sm:text-base md:text-lg lg:text-base xl:text-xs 2xl:text-base text-muted-foreground leading-relaxed px-2 sm:px-0">
              {success 
                ? 'Your password has been reset successfully. Redirecting to login...'
                : 'Enter your new password below.'
              }
            </p>
          </div>

          {/* Success Message */}
          {success && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-green-50/80 dark:bg-green-900/20 border border-green-200/70 dark:border-green-800/60 rounded-2xl p-4"
            >
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                <p className="text-sm text-green-600 dark:text-green-400">
                  Password reset successful! Redirecting to login...
                </p>
              </div>
            </motion.div>
          )}

          {/* Error Message */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-red-50/80 dark:bg-red-900/20 border border-red-200/70 dark:border-red-800/60 rounded-2xl p-4"
            >
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </motion.div>
          )}

          {/* Form */}
          {!success && token && (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 sm:space-y-6">
              <div className="space-y-3 sm:space-y-4">
                {/* New Password */}
                <div>
                  <label htmlFor="new_password" className="block text-xs sm:text-sm md:text-base lg:text-sm xl:text-xs 2xl:text-sm font-medium text-foreground mb-1 sm:mb-2">
                    New Password
                  </label>
                  <div className="relative mt-1 sm:mt-2">
                    <Input
                      {...register('new_password')}
                      id="new_password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Enter your new password"
                      className="w-full pl-8 sm:pl-10 pr-8 sm:pr-10 py-2.5 sm:py-3 text-sm sm:text-sm md:text-sm lg:text-sm xl:text-sm 2xl:text-sm bg-background/80 border border-border/60 rounded-2xl focus:border-saramsa-brand/50 focus:ring-2 focus:ring-saramsa-brand/20 focus:outline-none transition-all duration-300 text-foreground placeholder:text-muted-foreground shadow-[inset_0_1px_2px_rgba(0,0,0,0.05)] dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.4)]"
                    />
                    <Lock className="absolute left-2.5 sm:left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 sm:w-4 sm:h-4 text-muted-foreground" />
                    <Button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      variant="ghost"
                      size="icon"
                      className="absolute right-2.5 sm:right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-saramsa-brand"
                    >
                      {showPassword ? <EyeOff className="w-3.5 h-3.5 sm:w-4 sm:h-4" /> : <Eye className="w-3.5 h-3.5 sm:w-4 sm:h-4" />}
                    </Button>
                  </div>
                  {errors.new_password && (
                    <p className="mt-1 text-xs sm:text-sm text-red-500">{errors.new_password.message}</p>
                  )}
                </div>

                {/* Confirm Password */}
                <div>
                  <label htmlFor="confirm_password" className="block text-xs sm:text-sm md:text-base lg:text-sm xl:text-xs 2xl:text-sm font-medium text-foreground mb-1 sm:mb-2">
                    Confirm Password
                  </label>
                  <div className="relative mt-1 sm:mt-2">
                    <Input
                      {...register('confirm_password')}
                      id="confirm_password"
                      type={showConfirmPassword ? 'text' : 'password'}
                      placeholder="Confirm your new password"
                      className="w-full pl-8 sm:pl-10 pr-8 sm:pr-10 py-2.5 sm:py-3 text-sm sm:text-sm md:text-sm lg:text-sm xl:text-sm 2xl:text-sm bg-background/80 border border-border/60 rounded-2xl focus:border-saramsa-brand/50 focus:ring-2 focus:ring-saramsa-brand/20 focus:outline-none transition-all duration-300 text-foreground placeholder:text-muted-foreground shadow-[inset_0_1px_2px_rgba(0,0,0,0.05)] dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.4)]"
                    />
                    <Lock className="absolute left-2.5 sm:left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 sm:w-4 sm:h-4 text-muted-foreground" />
                    <Button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      variant="ghost"
                      size="icon"
                      className="absolute right-2.5 sm:right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-saramsa-brand"
                    >
                      {showConfirmPassword ? <EyeOff className="w-3.5 h-3.5 sm:w-4 sm:h-4" /> : <Eye className="w-3.5 h-3.5 sm:w-4 sm:h-4" />}
                    </Button>
                  </div>
                  {errors.confirm_password && (
                    <p className="mt-1 text-xs sm:text-sm text-red-500">{errors.confirm_password.message}</p>
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
                    Reset Password
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
        </motion.div>
      </div>
    </div>
  );
}


export default function ResetPasswordPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="w-8 h-8 border-4 border-saramsa-brand/30 border-t-saramsa-brand rounded-full animate-spin" />
      </div>
    }>
      <ResetPasswordContent />
    </Suspense>
  );
}


