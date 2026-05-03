'use client';

import { useState, useEffect, useRef, Suspense } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Eye, EyeOff, Mail, Lock, ArrowRight, Building2 } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import dynamic from 'next/dynamic';
import { AINodes, AIProcessing } from '@/components/ui/animations';

const BrandLogo = dynamic(
  () => import('@/components/ui/brand-logo').then(mod => mod.BrandLogo),
  { ssr: false }
);

const ThemeToggle = dynamic(
  () => import('@/components/ui/theme-toggle').then(mod => mod.ThemeToggle),
  { ssr: false }
);

import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/lib/useAuth';
import * as authApi from '@/lib/auth';
import type { InviteContext } from '@/lib/auth';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

const registerSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  otp: z.string().default(''),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  confirmPassword: z.string().min(1, 'Please confirm your password'),
  workspace_name: z.string().default(''),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

type RegisterFormData = z.input<typeof registerSchema>;

function RegisterPageInner() {
  const searchParams = useSearchParams();
  const inviteToken = searchParams?.get('invite') || '';

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [otpSent, setOtpSent] = useState(false);
  const [otpSending, setOtpSending] = useState(false);
  const [otpMessage, setOtpMessage] = useState<string | null>(null);
  const [otpCooldown, setOtpCooldown] = useState(0);
  const [invite, setInvite] = useState<InviteContext | null>(null);
  const [inviteLoading, setInviteLoading] = useState<boolean>(!!inviteToken);
  const [inviteError, setInviteError] = useState<string | null>(null);
  const otpInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();
  const { register: registerUser } = useAuth();

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const watchedEmail = watch('email');

  // Look up the invite once on mount so we can lock the email field and
  // skip OTP / workspace fields. If the lookup fails (expired, revoked,
  // wrong token) we surface a clean error and prevent submission.
  useEffect(() => {
    if (!inviteToken) return;
    let cancelled = false;
    (async () => {
      try {
        const data = await authApi.lookupInvite(inviteToken);
        if (cancelled) return;
        setInvite(data);
        setValue('email', data.email);
        setInviteError(null);
      } catch (err: any) {
        if (cancelled) return;
        setInviteError(err?.message || 'This invite link is invalid.');
      } finally {
        if (!cancelled) setInviteLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [inviteToken, setValue]);

  useEffect(() => {
    if (otpCooldown <= 0) return;
    const interval = setInterval(() => {
      setOtpCooldown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, [otpCooldown]);

  const handleSendOtp = async () => {
    if (!watchedEmail) {
      setError('Please enter your email address first.');
      return;
    }
    setOtpSending(true);
    setError(null);
    setOtpMessage(null);
    try {
      const result = await authApi.requestRegistrationOtp(watchedEmail);
      setOtpSent(true);
      setOtpCooldown(result.cooldown_seconds || 60);
      setOtpMessage('Code sent. Check your email.');
      setTimeout(() => otpInputRef.current?.focus(), 350);
    } catch (err: any) {
      setError(err?.message || 'Failed to send code.');
    } finally {
      setOtpSending(false);
    }
  };

  const onSubmit = async (data: RegisterFormData) => {
    if (invite) {
      // Invite signup: skip OTP + workspace name validation.
    } else {
      if (!otpSent) {
        setError('Please verify your email by clicking "Send code" first.');
        return;
      }
      if (!data.otp || !/^\d{6}$/.test(data.otp)) {
        setError('Please enter a valid 6-digit numeric verification code.');
        return;
      }
      if (!data.workspace_name?.trim()) {
        setError('Please enter a workspace name (your company name works well).');
        return;
      }
    }
    setIsLoading(true);
    setError(null);

    try {
      const result = await registerUser({
        email: data.email,
        otp: invite ? '' : data.otp,
        password: data.password,
        confirmPassword: data.confirmPassword,
        workspace_name: invite ? '' : data.workspace_name?.trim() || '',
        invite_token: inviteToken || '',
      });

      if (result.success) {
        // Brand new self-serve users go to config to wire their first
        // integration. Invite users land on the dashboard since the
        // workspace is already set up by the inviter.
        router.push(invite ? '/projects' : '/config/');
      } else {
        setError(result.error || 'Registration failed. Please try again.');
      }
    } catch (err: any) {
      console.error('Register error:', err);
      setError(err?.message || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-background text-foreground transition-colors duration-300 relative">
      <div className="fixed top-3 right-3 sm:top-4 sm:right-4 md:top-6 md:right-6 z-50">
        <ThemeToggle />
      </div>

      {/* Left visual pane */}
      <div className="hidden md:flex md:w-full lg:w-1/2 relative bg-gradient-to-br from-background via-secondary/80 to-saramsa-brand/20 dark:from-background dark:via-muted/60 dark:to-accent/40 overflow-hidden min-h-[40vh] lg:min-h-screen">
        <div className="absolute inset-0 bg-gradient-to-br from-saramsa-brand/15 via-transparent to-saramsa-gradient-to/15 dark:from-saramsa-brand/10 dark:to-saramsa-gradient-to/10" />
        <div className="hidden lg:block">
          <AINodes />
        </div>
        <div className="relative z-10 flex flex-col justify-center px-6 md:px-8 lg:px-12 py-8 lg:py-0">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.5 }}
            className="max-w-md mx-auto lg:mx-0"
          >
            <h1 className="text-2xl md:text-3xl lg:text-4xl xl:text-2xl 2xl:text-4xl font-semibold mb-4 md:mb-6 text-foreground leading-tight">
              {invite ? `Joining ${invite.organization.name || 'a workspace'}` : 'Join Saramsa AI'}
            </h1>
            <p className="text-sm md:text-base lg:text-lg xl:text-sm 2xl:text-lg text-muted-foreground mb-6 md:mb-8 leading-relaxed">
              {invite
                ? `You were invited as ${invite.role}. Create your account to accept.`
                : 'Start transforming customer feedback into actionable insights and automated tasks.'}
            </p>
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
                  <div className="w-2 h-2 bg-saramsa-brand rounded-full animate-pulse-glow shadow-[0_0_16px_rgba(139,95,191,0.45)] flex-shrink-0" />
                  <span className="text-sm md:text-base xl:text-xs text-muted-foreground">{feature}</span>
                </motion.div>
              ))}
            </div>
            <div className="hidden lg:block">
              <AIProcessing
                text={invite ? 'Adding you to workspace' : 'Setting up workspace'}
                className="mt-6 flex items-center gap-2 text-saramsa-brand"
              />
            </div>
          </motion.div>
        </div>
      </div>

      {/* Right form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-2 sm:p-3 md:p-5 bg-card md:border-l border-border dark:border-border/60 dark:bg-card/70 relative min-h-screen">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8 }}
          className="w-full max-w-[420px] mx-auto space-y-2.5 sm:space-y-3"
        >
          <div className="text-center">
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="mb-1.5 sm:mb-2"
            >
              <BrandLogo size="md" className="justify-center" />
            </motion.div>
          </div>

          <div className="text-center">
            <h2 className="text-lg sm:text-xl md:text-2xl font-semibold text-foreground leading-tight">
              {invite ? 'Accept invitation' : 'Create your account'}
            </h2>
            {invite && invite.organization.name && (
              <p className="mt-1 inline-flex items-center gap-1.5 text-xs text-muted-foreground">
                <Building2 className="h-3.5 w-3.5" />
                Joining <span className="font-medium text-foreground">{invite.organization.name}</span>
              </p>
            )}
          </div>

          {inviteError && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-destructive/10 border border-destructive/20 rounded-2xl p-4"
            >
              <p className="text-sm text-destructive">{inviteError}</p>
            </motion.div>
          )}

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-destructive/10 border border-destructive/20 rounded-2xl p-4"
            >
              <p className="text-sm text-destructive">{error}</p>
            </motion.div>
          )}

          {!inviteError && (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-2 sm:space-y-2.5">
              <div className="space-y-1.5 sm:space-y-2">
                {/* Email + Send Code (OTP block hidden when invite present) */}
                <div>
                  <label htmlFor="email" className="block text-xs sm:text-sm font-medium text-foreground mb-1 sm:mb-2">
                    Email address
                  </label>
                  <div className="flex items-center gap-2">
                    <div className="relative flex-1">
                      <Input
                        {...register('email')}
                        id="email"
                        type="email"
                        readOnly={!!invite}
                        placeholder="Enter your email"
                        className="w-full pl-8 sm:pl-10 pr-3 py-1.5 sm:py-2 text-sm bg-background border border-border rounded-2xl focus:border-saramsa-brand/50 focus:ring-2 focus:ring-saramsa-brand/20 focus:outline-none transition-all duration-300 text-foreground placeholder:text-muted-foreground shadow-[inset_0_1px_2px_rgba(0,0,0,0.06)] dark:bg-background/80 dark:border-border/60 dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.4)] disabled:opacity-70"
                      />
                      <Mail className="absolute left-2.5 sm:left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 sm:w-4 sm:h-4 text-muted-foreground" />
                    </div>
                    {!invite && (
                      <Button
                        type="button"
                        onClick={handleSendOtp}
                        disabled={otpSending || otpCooldown > 0}
                        variant="outline"
                        className="whitespace-nowrap h-9 px-3 text-xs sm:text-sm flex-shrink-0"
                      >
                        {otpSending ? (
                          <span className="flex items-center gap-1.5">
                            <span className="w-3 h-3 border-2 border-muted border-t-saramsa-brand rounded-full animate-spin" />
                            Sending…
                          </span>
                        ) : otpCooldown > 0 ? (
                          `Resend in ${otpCooldown}s`
                        ) : otpSent ? (
                          'Resend code'
                        ) : (
                          'Send code'
                        )}
                      </Button>
                    )}
                  </div>
                  {errors.email && (
                    <p className="mt-1 text-xs sm:text-sm text-destructive">{errors.email.message}</p>
                  )}
                  {!invite && otpMessage && (
                    <p className="mt-1 text-xs sm:text-sm text-green-600">{otpMessage}</p>
                  )}
                </div>

                {/* OTP appears only after Send Code (and never on invite signup) */}
                {!invite && otpSent && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    transition={{ duration: 0.3 }}
                  >
                    <label htmlFor="otp" className="block text-xs sm:text-sm font-medium text-foreground mb-1 sm:mb-2">
                      Verification code
                    </label>
                    <Input
                      {...register('otp')}
                      ref={(e) => {
                        register('otp').ref(e);
                        (otpInputRef as React.MutableRefObject<HTMLInputElement | null>).current = e;
                      }}
                      id="otp"
                      type="text"
                      inputMode="numeric"
                      maxLength={6}
                      autoFocus
                      placeholder="Enter 6-digit code"
                      className="w-full pl-3 py-1.5 sm:py-2 text-sm tracking-widest bg-background/80 border border-border/60 rounded-2xl focus:border-saramsa-brand/50 focus:ring-2 focus:ring-saramsa-brand/20 focus:outline-none transition-all duration-300 text-foreground placeholder:text-muted-foreground placeholder:tracking-normal shadow-[inset_0_1px_2px_rgba(0,0,0,0.05)] dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.4)]"
                    />
                  </motion.div>
                )}

                {/* Workspace name (Pattern A — first workspace = company). Hidden on invite signup. */}
                {!invite && (
                  <div>
                    <label htmlFor="workspace_name" className="block text-xs sm:text-sm font-medium text-foreground mb-1 sm:mb-2">
                      Workspace name
                    </label>
                    <div className="relative">
                      <Input
                        {...register('workspace_name')}
                        id="workspace_name"
                        type="text"
                        placeholder="e.g. Acme Corp"
                        className="w-full pl-8 sm:pl-10 pr-3 py-1.5 sm:py-2 text-sm bg-background border border-border rounded-2xl focus:border-saramsa-brand/50 focus:ring-2 focus:ring-saramsa-brand/20 focus:outline-none transition-all duration-300 text-foreground placeholder:text-muted-foreground shadow-[inset_0_1px_2px_rgba(0,0,0,0.06)] dark:bg-background/80 dark:border-border/60 dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.4)]"
                      />
                      <Building2 className="absolute left-2.5 sm:left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 sm:w-4 sm:h-4 text-muted-foreground" />
                    </div>
                    <p className="mt-1 text-[11px] text-muted-foreground">Use your company name. You can rename it later.</p>
                  </div>
                )}

                {/* Password */}
                <div>
                  <label htmlFor="password" className="block text-xs sm:text-sm font-medium text-foreground mb-1 sm:mb-2">
                    Password
                  </label>
                  <div className="relative">
                    <Input
                      {...register('password')}
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Create a password"
                      className="w-full pl-8 sm:pl-10 pr-8 sm:pr-10 py-1.5 sm:py-2 text-sm bg-background border border-border rounded-2xl focus:border-saramsa-brand/50 focus:ring-2 focus:ring-saramsa-brand/20 focus:outline-none transition-all duration-300 text-foreground placeholder:text-muted-foreground shadow-[inset_0_1px_2px_rgba(0,0,0,0.06)] dark:bg-background/80 dark:border-border/60 dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.4)]"
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
                  {errors.password && (
                    <p className="mt-1 text-xs sm:text-sm text-destructive">{errors.password.message}</p>
                  )}
                </div>

                {/* Confirm password */}
                <div>
                  <label htmlFor="confirmPassword" className="block text-xs sm:text-sm font-medium text-foreground mb-1 sm:mb-2">
                    Confirm Password
                  </label>
                  <div className="relative">
                    <Input
                      {...register('confirmPassword')}
                      id="confirmPassword"
                      type={showConfirmPassword ? 'text' : 'password'}
                      placeholder="Confirm your password"
                      className="w-full pl-8 sm:pl-10 pr-8 sm:pr-10 py-1.5 sm:py-2 text-sm bg-background border border-border rounded-2xl focus:border-saramsa-brand/50 focus:ring-2 focus:ring-saramsa-brand/20 focus:outline-none transition-all duration-300 text-foreground placeholder:text-muted-foreground shadow-[inset_0_1px_2px_rgba(0,0,0,0.06)] dark:bg-background/80 dark:border-border/60 dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.4)]"
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
                  {errors.confirmPassword && (
                    <p className="mt-1 text-xs sm:text-sm text-destructive">{errors.confirmPassword.message}</p>
                  )}
                </div>
              </div>

              <Button
                type="submit"
                disabled={isLoading || inviteLoading}
                variant="saramsa"
                className="w-full py-1.5 sm:py-2 text-sm group"
              >
                {isLoading || inviteLoading ? (
                  <div className="w-4 h-4 sm:w-5 sm:h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mx-auto" />
                ) : (
                  <>
                    {invite ? 'Accept & create account' : 'Create Account'}
                    <ArrowRight className="ml-2 w-3.5 h-3.5 sm:w-4 sm:h-4 group-hover:translate-x-1 transition-transform inline" />
                  </>
                )}
              </Button>

              <div className="text-center">
                <p className="text-xs sm:text-sm text-muted-foreground">
                  Already have an account?{' '}
                  <Link
                    href={invite ? `/login?invite=${encodeURIComponent(inviteToken)}` : '/login'}
                    className="text-saramsa-brand hover:text-saramsa-brand-hover font-medium transition-colors"
                  >
                    Sign in
                  </Link>
                </p>
              </div>
            </form>
          )}
        </motion.div>
      </div>
    </div>
  );
}

export default function RegisterPage() {
  return (
    <Suspense fallback={null}>
      <RegisterPageInner />
    </Suspense>
  );
}
