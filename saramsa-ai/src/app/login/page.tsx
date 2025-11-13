'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Eye, EyeOff, Mail, Lock, ArrowRight } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/useAuth';
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
const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const [mounted, setMounted] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const { login } = useAuth();

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
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });


  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await login({
        username: data.username,
        password: data.password,
      });
      
      if (result.success) {
        // After successful login, fetch user's projects and route accordingly
        try {
          const res = await apiRequest('get', '/projects/list/', undefined, true);
          const projects = res.data?.projects || [];
          if (projects.length > 0) {
            const first = projects[0];
            const projectId = first?.id || first?.project_id;
            if (projectId && typeof window !== 'undefined') {
              localStorage.setItem('project_id', projectId);
              if (first?.organization) localStorage.setItem('azure_organization', first.organization);
              if (first?.project_name) localStorage.setItem('azure_project_name', first.project_name);
            }
            router.push('/dashboard');
          } else {
            // If no projects exist, still prefer dashboard if Azure is configured
            try {
              const saved = await apiRequest('get', '/workitems/azure/config', undefined, true);
              if (saved.data?.success) {
                router.push('/dashboard');
              } else {
                router.push('/config');
              }
            } catch {
              router.push('/config');
            }
          }
        } catch {
          // On error fetching projects, go to dashboard shell; config if needed will be prompted there
          router.push('/dashboard');
        }
      } else {
        setError(result.error || 'Login failed. Please check your credentials and try again.');
      }
    } catch (error: unknown) {
      console.error('Login error:', error);
      setError('Login failed. Please check your credentials and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Removed unused handleThirdPartyLogin function

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
        <div className="hidden lg:block">
          <DataStream />
        </div>
        
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

      {/* Right Login Form */}
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
            <p className="mt-2 sm:mt-3 text-sm sm:text-base md:text-lg lg:text-base xl:text-xs 2xl:text-base text-muted-foreground leading-relaxed px-2 sm:px-0">
              AI-driven feedback analysis and task automation for Product Managers
            </p>
          </div>

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
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 sm:space-y-6">
            <div className="space-y-3 sm:space-y-4">
              {/* Username */}
              <div>
                <label htmlFor="username" className="block text-xs sm:text-sm md:text-base lg:text-sm xl:text-xs 2xl:text-sm font-medium text-gray-900 dark:text-white mb-1 sm:mb-2">
                  Username
                </label>
                <div className="relative mt-1 sm:mt-2">
                  <input
                    {...register('username')}
                    id="username"
                    type="text"
                    placeholder="Enter your username"
                    className="w-full pl-8 sm:pl-10 pr-3 py-2.5 sm:py-3 text-sm sm:text-sm md:text-sm lg:text-sm xl:text-sm 2xl:text-sm bg-gray-50 dark:bg-gray-800 border border-gray-200 
                    dark:border-gray-700 rounded-lg focus:border-[#E603EB] focus:ring-[#E603EB]/20 focus:outline-none transition-all duration-300 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                  />
                  <Mail className="absolute left-2.5 sm:left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 sm:w-4 sm:h-4 text-gray-400" />
                </div>
                {errors.username && (
                  <p className="mt-1 text-xs sm:text-sm text-red-500">{errors.username.message}</p>
                )}
              </div>

              {/* Password */}
              <div>
                <label htmlFor="password" className="block text-xs sm:text-sm md:text-base lg:text-sm xl:text-xs 2xl:text-sm font-medium text-gray-900 dark:text-white mb-1 sm:mb-2">
                  Password
                </label>
                <div className="relative mt-1 sm:mt-2">
                  <input
                    {...register('password')}
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Enter your password"
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
                  <p className="mt-1 text-xs sm:text-sm text-red-500">{errors.password.message}</p>
                )}
              </div>
            </div>

            {/* Forgot Password */}
            <div className="text-right">
              <button
                type="button"
                className="text-xs sm:text-sm md:text-base lg:text-sm xl:text-xs 2xl:text-sm text-[#E603EB] hover:text-[#E603EB]/80 transition-colors"
              >
                Forgot password?
              </button>
            </div>

            {/* Login CTA */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-saramsa-brand to-saramsa-gradient-to hover:from-saramsa-brand-hover hover:to-saramsa-gradient-to text-white py-2.5 sm:py-3 px-4 rounded-lg text-sm sm:text-base md:text-lg lg:text-base xl:text-xs 2xl:text-base font-medium shadow-lg hover:shadow-xl transition-all duration-300 group disabled:opacity-50 disabled:cursor-not-allowed animate-glow"
            >
              {isLoading ? (
                <div className="w-4 h-4 sm:w-5 sm:h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mx-auto" />
              ) : (
                <>
                  Login
                  <ArrowRight className="ml-2 w-3.5 h-3.5 sm:w-4 sm:h-4 group-hover:translate-x-1 transition-transform inline" />
                </>
              )}
            </button>

            {/* Register Link */}
            <div className="text-center">
              <p className="text-xs sm:text-sm md:text-base lg:text-sm xl:text-xs 2xl:text-sm text-gray-600 dark:text-gray-400">
                New to Saramsa AI?{' '}
                <Link
                  href="/register"
                  className="text-[#E603EB] hover:text-[#E603EB]/80 font-medium transition-colors"
                >
                  Create an account
                </Link>
              </p>
            </div>
          </form>
        </motion.div>
      </div>
    </div>
  );
}
