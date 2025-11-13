'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Eye, EyeOff, Mail, Lock, User, ArrowRight, Check, X } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import dynamic from 'next/dynamic';
import { DataStream, AINodes, AIProcessing } from '@/components/ui/animations';

// Lazy-load components to avoid SSR issues

const BrandLogo = dynamic(
  () => import('@/components/ui/brand-logo').then(mod => mod.BrandLogo),
  { ssr: false }
);

const ThemeToggle = dynamic(
  () => import('@/components/ui/theme-toggle').then(mod => mod.ThemeToggle),
  { ssr: false }
);

import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/useAuth';
import * as authApi from '@/lib/auth';

// Form validation schema
const registerSchema = z.object({
  username: z.string().min(2, 'User name must be at least 2 characters'),
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  confirmPassword: z.string().min(1, 'Please confirm your password'),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

type RegisterFormData = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [usernameStatus, setUsernameStatus] = useState<'idle' | 'checking' | 'available' | 'unavailable'>('idle');
  const router = useRouter();
  const { register: registerUser } = useAuth();

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const watchedUsername = watch('username');

  // Check username availability when username changes
  useEffect(() => {
    const checkUsername = async () => {
      if (watchedUsername && watchedUsername.length >= 2) {
        setUsernameStatus('checking');
        try {
          const response = await authApi.checkUsername(watchedUsername);
          setUsernameStatus(response.available ? 'available' : 'unavailable');
        } catch {
          setUsernameStatus('unavailable');
        }
      } else {
        setUsernameStatus('idle');
      }
    };

    const timeoutId = setTimeout(checkUsername, 500);
    return () => clearTimeout(timeoutId);
  }, [watchedUsername]);

  const onSubmit = async (data: RegisterFormData) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await registerUser({
        username: data.username,
        email: data.email,
        password: data.password,
        confirmPassword: data.confirmPassword,
      });
      
      if (result.success) {
        // brand new users go to config
        router.push('/config');
      } else {
        setError(result.error || 'Registration failed. Please try again.');
      }
    } catch (error: unknown) {
      console.error('Register error:', error);
      setError('Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

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
        <div className="hidden lg:block">
          <DataStream />
        </div>
        
        {/* AI Processing Nodes - Hidden on tablet/iPad */}
        <div className="hidden lg:block">
          <AINodes />
        </div>
        
        {/* Content overlay */}
        <div className="relative z-10 flex flex-col justify-center px-6 md:px-8 lg:px-12 py-8 lg:py-0">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.5 }}
            className="max-w-md mx-auto lg:mx-0"
          >
            <h1 className="text-2xl md:text-3xl lg:text-4xl xl:text-2xl 2xl:text-4xl font-bold mb-4 md:mb-6 text-foreground leading-tight">
              Join Saramsa AI
            </h1>
            <p className="text-sm md:text-base lg:text-lg xl:text-sm 2xl:text-lg text-muted-foreground mb-6 md:mb-8 leading-relaxed">
              Start transforming customer feedback into actionable insights and automated tasks.
            </p>
            
            {/* Feature highlights */}
            <div className="space-y-3 md:space-y-4">
              {[
                'AI-powered feedback analysis',
                'Automated task creation',
                'Smart priority recommendations',
                'Real-time insights dashboard',
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
            
            {/* Status indicator - Hidden on tablet/iPad */}
            <div className="hidden lg:block">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.8, delay: 2 }}
                className="mt-8 p-4 bg-card/80 rounded-lg backdrop-blur-sm border border-border animate-glow"
              >
                <div className="flex items-center gap-3">
                  <motion.div
                    animate={{ scale: [1, 1.1, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="w-8 h-8 bg-gradient-to-br from-saramsa-gradient-from to-saramsa-gradient-to rounded-full flex items-center justify-center shadow-lg animate-pulse-glow"
                  >
                    <div className="w-3 h-3 bg-white rounded-full" />
                  </motion.div>
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      AI Assistant Ready
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Waiting to analyze your feedback
                    </p>
                  </div>
                </div>
              </motion.div>
            </div>
            
            {/* Registration Progress Animation - Hidden on tablet/iPad */}
            <div className="hidden lg:block">
              <AIProcessing 
                text="Setting up workspace" 
                className="mt-6 flex items-center gap-2 text-saramsa-brand" 
              />
            </div>
          </motion.div>
        </div>
      </div>

      {/* Right Register Form */}
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
            <h2 className="text-xl sm:text-2xl md:text-3xl lg:text-xl xl:text-lg 2xl:text-3xl font-bold text-foreground leading-tight">
              Create Your Account
            </h2>
            <p className="mt-2 sm:mt-3  lg:mt-2 xl:mt-3 text-sm sm:text-base md:text-lg lg:text-sm xl:text-xs 2xl:text-base text-muted-foreground leading-relaxed px-2 sm:px-0">
             Use AI to transform feedback
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-destructive/10 border border-destructive/20 rounded-lg p-4"
            >
              <p className="text-sm text-destructive">{error}</p>
            </motion.div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 sm:space-y-6">
            <div className="space-y-3 sm:space-y-4">
              {/* Username */}
              <div>
                <label htmlFor="username" className="block text-xs sm:text-sm md:text-base lg:text-sm xl:text-xs 2xl:text-sm font-medium text-gray-900 dark:text-white mb-1 sm:mb-2">
                  Username
                </label>
                <div className="relative">
                  <input
                    {...register('username')}
                    id="username"
                    type="text"
                    placeholder="Choose a username"
                    className={`w-full pl-8 sm:pl-10 pr-8 sm:pr-10 py-2.5 sm:py-3 text-sm sm:text-sm md:text-sm lg:text-sm xl:text-sm 2xl:text-sm bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:border-[#E603EB] focus:ring-[#E603EB]/20 focus:outline-none transition-all duration-300 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 ${
                      usernameStatus === 'available' ? 'border-green-500' : 
                      usernameStatus === 'unavailable' ? 'border-destructive' : ''
                    }`}
                  />
                  <User className="absolute left-2.5 sm:left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 sm:w-4 sm:h-4 text-gray-400" />
                  
                  {/* Username status indicator */}
                  {usernameStatus === 'checking' && (
                    <div className="absolute right-2.5 sm:right-3 top-1/2 -translate-y-1/2">
                      <div className="w-3.5 h-3.5 sm:w-4 sm:h-4 border-2 border-muted border-t-saramsa-brand rounded-full animate-spin" />
                    </div>
                  )}
                  {usernameStatus === 'available' && (
                    <Check className="absolute right-2.5 sm:right-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 sm:w-4 sm:h-4 text-green-500" />
                  )}
                  {usernameStatus === 'unavailable' && (
                    <X className="absolute right-2.5 sm:right-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 sm:w-4 sm:h-4 text-red-500" />
                  )}
                </div>
                {errors.username && (
                  <p className="mt-1 text-xs sm:text-sm text-destructive">{errors.username.message}</p>
                )}
                {usernameStatus === 'available' && (
                  <p className="mt-1 text-xs sm:text-sm text-green-600">Username is available</p>
                )}
                {usernameStatus === 'unavailable' && watchedUsername && watchedUsername.length >= 2 && (
                  <p className="mt-1 text-xs sm:text-sm text-destructive">Username is already taken</p>
                )}
              </div>

              {/* Email */}
              <div>
                <label htmlFor="email" className="block text-xs sm:text-sm md:text-base lg:text-sm xl:text-xs 2xl:text-sm font-medium text-gray-900 dark:text-white mb-1 sm:mb-2">
                  Email address
                </label>
                <div className="relative">
                  <input
                    {...register('email')}
                    id="email"
                    type="email"
                    placeholder="Enter your email"
                    className="w-full pl-8 sm:pl-10 pr-3 py-2.5 sm:py-3 text-sm sm:text-sm md:text-sm lg:text-sm xl:text-sm 2xl:text-sm bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:border-[#E603EB] focus:ring-[#E603EB]/20 focus:outline-none transition-all duration-300 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                  />
                  <Mail className="absolute left-2.5 sm:left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 sm:w-4 sm:h-4 text-gray-400" />
                </div>
                {errors.email && (
                  <p className="mt-1 text-xs sm:text-sm text-destructive">{errors.email.message}</p>
                )}
              </div>

              {/* Password */}
              <div>
                <label htmlFor="password" className="block text-xs sm:text-sm md:text-base lg:text-sm xl:text-xs 2xl:text-sm font-medium text-gray-900 dark:text-white mb-1 sm:mb-2">
                  Password
                </label>
                <div className="relative">
                  <input
                    {...register('password')}
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Create a password"
                    className="w-full pl-8 sm:pl-10 pr-8 sm:pr-10 py-2.5 sm:py-3 text-sm sm:text-base md:text-lg lg:text-base xl:text-xs 2xl:text-base bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:border-[#E603EB] focus:ring-[#E603EB]/20 focus:outline-none transition-all duration-300 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                  />
                  <Lock className="absolute left-2.5 sm:left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 sm:w-4 sm:h-4 text-gray-400" />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-2.5 sm:right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-[#E603EB] transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-3.5 h-3.5 sm:w-4 sm:h-4" /> : <Eye className="w-3.5 h-3.5 sm:w-4 sm:h-4" />}
                  </button>
                </div>
                {errors.password && (
                  <p className="mt-1 text-xs sm:text-sm text-destructive">{errors.password.message}</p>
                )}
              </div>

              {/* Confirm Password */}
              <div>
                <label htmlFor="confirmPassword" className="block text-xs sm:text-sm md:text-base lg:text-sm xl:text-xs 2xl:text-sm font-medium text-gray-900 dark:text-white mb-1 sm:mb-2">
                  Confirm Password
                </label>
                <div className="relative">
                  <input
                    {...register('confirmPassword')}
                    id="confirmPassword"
                    type={showConfirmPassword ? 'text' : 'password'}
                    placeholder="Confirm your password"
                    className="w-full pl-8 sm:pl-10 pr-8 sm:pr-10 py-2.5 sm:py-3 text-sm sm:text-base md:text-lg lg:text-base xl:text-xs 2xl:text-base bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:border-[#E603EB] focus:ring-[#E603EB]/20 focus:outline-none transition-all duration-300 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                  />
                  <Lock className="absolute left-2.5 sm:left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 sm:w-4 sm:h-4 text-gray-400" />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-2.5 sm:right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-[#E603EB] transition-colors"
                  >
                    {showConfirmPassword ? <EyeOff className="w-3.5 h-3.5 sm:w-4 sm:h-4" /> : <Eye className="w-3.5 h-3.5 sm:w-4 sm:h-4" />}
                  </button>
                </div>
                {errors.confirmPassword && (
                  <p className="mt-1 text-xs sm:text-sm text-destructive">{errors.confirmPassword.message}</p>
                )}
              </div>
            </div>

            {/* Create Account Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-saramsa-brand to-saramsa-gradient-to hover:from-saramsa-brand hover:to-saramsa-gradient-to text-white py-2.5 sm:py-3 px-4 rounded-lg text-sm sm:text-base md:text-lg lg:text-base xl:text-xs 2xl:text-base font-medium shadow-lg hover:shadow-xl transition-all duration-300 group disabled:opacity-50 disabled:cursor-not-allowed animate-glow"
            >
              {isLoading ? (
                <div className="w-4 h-4 sm:w-5 sm:h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mx-auto" />
              ) : (
                <>
                  Create Account
                  <ArrowRight className="ml-2 w-3.5 h-3.5 sm:w-4 sm:h-4 group-hover:translate-x-1 transition-transform inline" />
                </>
              )}
            </button>

            {/* Login Link */}
            <div className="text-center">
              <p className="text-xs sm:text-sm md:text-base lg:text-sm xl:text-xs 2xl:text-sm text-gray-600 dark:text-gray-400">
                Already have an account?{' '}
                <Link
                  href="/login"
                  className="text-[#E603EB] hover:text-[#E603EB]/80 font-medium transition-colors"
                >
                  Sign in
                </Link>
              </p>
            </div>
          </form>
        </motion.div>
      </div>
    </div>
  );
} 