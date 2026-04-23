'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  Mail,
  User,
  Phone,
  Globe,
  Briefcase,
  MapPin,
  ArrowRight,
  CheckCircle2,
} from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import dynamic from 'next/dynamic';
import { TaskCards, AIProcessing } from '@/components/ui/animations';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

const ThemeToggle = dynamic(
  () => import('@/components/ui/theme-toggle').then((mod) => mod.ThemeToggle),
  { ssr: false }
);

const FREE_EMAIL_DOMAINS = [
  'gmail.com',
  'yahoo.com',
  'hotmail.com',
  'outlook.com',
  'live.com',
  'aol.com',
  'icloud.com',
  'proton.me',
  'protonmail.com',
  'mail.com',
  'yandex.com',
  'gmx.com',
  'zoho.com',
];

const inviteSchema = z.object({
  email: z
    .string()
    .email('Please enter a valid email address')
    .refine((email) => {
      const domain = email.split('@')[1]?.toLowerCase();
      return !!domain && !FREE_EMAIL_DOMAINS.includes(domain);
    }, 'Please use your official work email, not a personal account'),
  country: z.string().min(2, 'Please enter your country'),
  name: z.string().min(2, 'Please enter your full name'),
  phone: z.string().min(6, 'Please enter a valid phone number'),
  jobFunction: z.string().min(2, 'Please enter your job function'),
  companyWebsite: z.string().min(3, 'Please enter your company website'),
});

type InviteFormData = z.infer<typeof inviteSchema>;

export default function SignupPage() {
  const [mounted, setMounted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<InviteFormData>({
    resolver: zodResolver(inviteSchema),
  });

  const onSubmit = async (data: InviteFormData) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('https://api.web3forms.com/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          access_key: 'be527df5-46bf-4cc4-983d-5c0cde08bf10',
          from_name: 'Saramsa.ai Invite Request',
          subject: `Invite request from ${data.name} (${data.companyWebsite})`,
          name: data.name,
          email: data.email,
          country: data.country,
          phone: data.phone,
          job_function: data.jobFunction,
          company_website: data.companyWebsite,
          message:
            `New invite request:\n\n` +
            `Name: ${data.name}\n` +
            `Email: ${data.email}\n` +
            `Country: ${data.country}\n` +
            `Phone: ${data.phone}\n` +
            `Job function: ${data.jobFunction}\n` +
            `Company website: ${data.companyWebsite}`,
        }),
      });

      const json = await response.json();
      if (json.success) {
        setSubmitted(true);
        reset();
      } else {
        setError(json.message || 'Something went wrong. Please try again.');
      }
    } catch (err) {
      console.error('Invite submission failed:', err);
      setError('We could not submit your request. Please try again in a moment.');
    } finally {
      setIsLoading(false);
    }
  };

  if (!mounted) return null;

  const inputBase =
    'w-full pl-10 pr-3 py-2.5 text-sm bg-background border border-border rounded-2xl focus:border-saramsa-brand/50 focus:ring-2 focus:ring-saramsa-brand/20 focus:outline-none transition-all duration-300 text-foreground placeholder:text-muted-foreground shadow-[inset_0_1px_2px_rgba(0,0,0,0.06)] dark:bg-background/80 dark:border-border/60 dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.4)]';
  const iconBase = 'absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground';
  const labelBase = 'block text-xs font-medium text-foreground mb-1.5';

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-background text-foreground transition-colors duration-300 relative">
      <div className="fixed top-3 right-3 sm:top-4 sm:right-4 md:top-6 md:right-6 z-50">
        <ThemeToggle />
      </div>

      {/* Left visual pane */}
      <div className="hidden md:flex md:w-full lg:w-1/2 relative bg-gradient-to-br from-background via-secondary/80 to-saramsa-brand/20 dark:from-background dark:via-muted/60 dark:to-accent/40 overflow-hidden min-h-[40vh] lg:min-h-screen">
        <div className="absolute inset-0 bg-gradient-to-br from-saramsa-brand/15 via-transparent to-saramsa-gradient-to/15 dark:from-saramsa-brand/10 dark:to-saramsa-gradient-to/10" />

        <div className="hidden lg:block">
          <TaskCards variant="login" />
        </div>

        <div className="relative z-10 flex flex-col justify-center px-6 md:px-8 lg:px-12 py-8 lg:py-0">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.4 }}
            className="max-w-md mx-auto lg:mx-0"
          >
            <h1 className="text-2xl md:text-3xl lg:text-4xl xl:text-2xl 2xl:text-4xl font-semibold mb-4 md:mb-6 text-foreground leading-tight">
              Built for product teams that ship
            </h1>
            <p className="text-sm md:text-base lg:text-lg xl:text-sm 2xl:text-lg text-muted-foreground mb-6 md:mb-8 leading-relaxed">
              Saramsa AI is in closed beta with a select group of companies. Tell us a bit about your team and we&apos;ll reach out when we&apos;re ready to support you.
            </p>
            <div className="hidden lg:block">
              <AIProcessing
                text="Vetting requests"
                className="mt-4 flex items-center gap-2 text-saramsa-brand"
              />
            </div>
          </motion.div>
        </div>
      </div>

      {/* Right form pane */}
      <div className="w-full lg:w-1/2 bg-card md:border-l border-border dark:border-border/60 dark:bg-card/70 relative overflow-y-auto lg:h-screen">
        <div className="min-h-full flex items-center justify-center p-4 sm:p-6 md:p-8 lg:p-10">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6 }}
          className="w-full max-w-md mx-auto space-y-6"
        >
          {submitted ? (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center py-8"
            >
              <div className="w-14 h-14 mx-auto mb-4 rounded-full bg-saramsa-brand/10 flex items-center justify-center">
                <CheckCircle2 className="w-7 h-7 text-saramsa-brand" />
              </div>
              <h2 className="text-lg font-semibold mb-2 text-foreground">
                Request received
              </h2>
              <p className="text-sm text-muted-foreground mb-6 leading-relaxed">
                Thanks — we&apos;ll reach out to you shortly at the email you provided.
              </p>
              <Link
                href="/login"
                className="text-sm text-saramsa-brand hover:text-saramsa-brand-hover font-medium transition-colors"
              >
                Back to login
              </Link>
            </motion.div>
          ) : (
            <>
              <div className="text-center">
                <h2 className="text-xl md:text-2xl font-semibold mb-2 text-foreground">
                  Request invite
                </h2>
                <p className="text-base md:text-lg text-muted-foreground leading-relaxed px-1 sm:px-0">
                  Hey there! We&apos;re now available by invite only. Please fill out this form, and we&apos;ll reach out to you as soon as we can.
                </p>
              </div>

              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-destructive/10 border border-destructive/20 rounded-2xl p-3"
                >
                  <p className="text-sm text-destructive">{error}</p>
                </motion.div>
              )}

              <form onSubmit={handleSubmit(onSubmit)} className="space-y-3.5">
                <div>
                  <label htmlFor="name" className={labelBase}>Full name</label>
                  <div className="relative">
                    <Input
                      {...register('name')}
                      id="name"
                      type="text"
                      placeholder="Jane Doe"
                      className={inputBase}
                    />
                    <User className={iconBase} />
                  </div>
                  {errors.name && (
                    <p className="mt-1 text-xs text-destructive">{errors.name.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="email" className={labelBase}>Official email</label>
                  <div className="relative">
                    <Input
                      {...register('email')}
                      id="email"
                      type="email"
                      placeholder="jane@company.com"
                      className={inputBase}
                    />
                    <Mail className={iconBase} />
                  </div>
                  {errors.email && (
                    <p className="mt-1 text-xs text-destructive">{errors.email.message}</p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label htmlFor="country" className={labelBase}>Country</label>
                    <div className="relative">
                      <Input
                        {...register('country')}
                        id="country"
                        type="text"
                        placeholder="India"
                        className={inputBase}
                      />
                      <MapPin className={iconBase} />
                    </div>
                    {errors.country && (
                      <p className="mt-1 text-xs text-destructive">{errors.country.message}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="phone" className={labelBase}>Phone</label>
                    <div className="relative">
                      <Input
                        {...register('phone')}
                        id="phone"
                        type="tel"
                        placeholder="+91 98765 43210"
                        className={inputBase}
                      />
                      <Phone className={iconBase} />
                    </div>
                    {errors.phone && (
                      <p className="mt-1 text-xs text-destructive">{errors.phone.message}</p>
                    )}
                  </div>
                </div>

                <div>
                  <label htmlFor="jobFunction" className={labelBase}>Job function</label>
                  <div className="relative">
                    <Input
                      {...register('jobFunction')}
                      id="jobFunction"
                      type="text"
                      placeholder="Product Manager"
                      className={inputBase}
                    />
                    <Briefcase className={iconBase} />
                  </div>
                  {errors.jobFunction && (
                    <p className="mt-1 text-xs text-destructive">{errors.jobFunction.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="companyWebsite" className={labelBase}>Company website</label>
                  <div className="relative">
                    <Input
                      {...register('companyWebsite')}
                      id="companyWebsite"
                      type="text"
                      placeholder="company.com"
                      className={inputBase}
                    />
                    <Globe className={iconBase} />
                  </div>
                  {errors.companyWebsite && (
                    <p className="mt-1 text-xs text-destructive">{errors.companyWebsite.message}</p>
                  )}
                </div>

                <Button
                  type="submit"
                  disabled={isLoading}
                  variant="saramsa"
                  className="w-full py-2.5 text-sm group mt-2"
                >
                  {isLoading ? (
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mx-auto" />
                  ) : (
                    <>
                      Request invite
                      <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform inline" />
                    </>
                  )}
                </Button>

                <div className="text-center pt-1">
                  <p className="text-xs text-muted-foreground">
                    Already have an account?{' '}
                    <Link
                      href="/login"
                      className="text-saramsa-brand hover:text-saramsa-brand-hover font-medium transition-colors"
                    >
                      Login
                    </Link>
                  </p>
                </div>
              </form>
            </>
          )}
        </motion.div>
        </div>
      </div>
    </div>
  );
}
