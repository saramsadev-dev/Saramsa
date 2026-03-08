'use client';

import { useState } from 'react';
import { useDispatch } from 'react-redux';
import type { AppDispatch } from '@/store/store';
import { createJiraIntegration } from '@/store/features/integrations/integrationsSlice';
import { motion } from 'framer-motion';
import { X, ExternalLink, Eye, EyeOff, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

interface JiraIntegrationFormProps {
  onClose: () => void;
  onSuccess: () => void;
}

export function JiraIntegrationForm({ onClose, onSuccess }: JiraIntegrationFormProps) {
  const dispatch = useDispatch<AppDispatch>();
  const [formData, setFormData] = useState({
    domain: '',
    email: '',
    api_token: '',
  });
  const [showToken, setShowToken] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<{ [key: string]: string }>({});

  const validateForm = () => {
    const errors: { [key: string]: string } = {};
    
    if (!formData.domain.trim()) {
      errors.domain = 'Jira domain is required';
    } else if (!formData.domain.match(/^[a-zA-Z0-9-]+$/)) {
      errors.domain = 'Invalid domain format. Use only letters, numbers, and hyphens.';
    }
    
    if (!formData.email.trim()) {
      errors.email = 'Email address is required';
    } else if (!formData.email.includes('@')) {
      errors.email = 'Please enter a valid email address';
    }
    
    if (!formData.api_token.trim()) {
      errors.api_token = 'API Token is required';
    } else if (formData.api_token.length < 10) {
      errors.api_token = 'API Token seems too short. Please check your token.';
    }
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      await dispatch(createJiraIntegration({
        domain: formData.domain.trim(),
        email: formData.email.trim(),
        api_token: formData.api_token.trim(),
      })).unwrap();
      
      onSuccess();
    } catch (err: any) {
      setError(err.message || 'Failed to connect to Jira');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear validation error when user starts typing
    if (validationErrors[field]) {
      setValidationErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="bg-card/90 dark:bg-card/95 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border/60 dark:border-border/60">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-saramsa-gradient-from to-saramsa-gradient-to rounded-xl flex items-center justify-center">
              <span className="text-white font-bold">J</span>
            </div>
            <div>
              <h2 className="text-xl font-semibold text-foreground dark:text-foreground">
                Connect Jira
              </h2>
              <p className="text-sm text-muted-foreground dark:text-muted-foreground">
                Add your Jira Cloud instance to import projects
              </p>
            </div>
          </div>
          <Button
            onClick={onClose}
            variant="ghost"
            size="icon"
            className="h-9 w-9 hover:bg-accent/60 dark:hover:bg-accent/60"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Error Display */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4"
            >
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-500" />
                <span className="text-red-700 dark:text-red-300">{error}</span>
              </div>
            </motion.div>
          )}

          {/* Jira Domain */}
          <div>
            <label className="block text-sm font-medium text-muted-foreground dark:text-muted-foreground mb-2">
              Jira Domain
            </label>
            <div className="flex items-center">
              <span className="text-muted-foreground dark:text-muted-foreground text-sm mr-2">https://</span>
              <Input
                type="text"
                value={formData.domain}
                onChange={(e) => handleInputChange('domain', e.target.value)}
                placeholder="yourcompany"
                className={`flex-1 px-4 py-3 rounded-xl border ${
                  validationErrors.domain
                    ? 'border-red-300 dark:border-red-600'
                    : 'border-border/60 dark:border-border/60'
                } bg-background/80 text-foreground dark:text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-saramsa-brand/30 focus:border-saramsa-brand/40`}
              />
              <span className="text-muted-foreground dark:text-muted-foreground text-sm ml-2">.atlassian.net</span>
            </div>
            {validationErrors.domain && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                {validationErrors.domain}
              </p>
            )}
            <p className="mt-1 text-sm text-muted-foreground dark:text-muted-foreground">
              Your Jira Cloud domain (without https:// or .atlassian.net)
            </p>
          </div>

          {/* Email */}
          <div>
            <label className="block text-sm font-medium text-muted-foreground dark:text-muted-foreground mb-2">
              Email Address
            </label>
            <Input
              type="email"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              placeholder="your.email@company.com"
              className={`w-full px-4 py-3 rounded-xl border ${
                validationErrors.email
                  ? 'border-red-300 dark:border-red-600'
                  : 'border-border/60 dark:border-border/60'
              } bg-background/80 text-foreground dark:text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-saramsa-brand/30 focus:border-saramsa-brand/40`}
            />
            {validationErrors.email && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                {validationErrors.email}
              </p>
            )}
            <p className="mt-1 text-sm text-muted-foreground dark:text-muted-foreground">
              The email address associated with your Jira account
            </p>
          </div>

          {/* API Token */}
          <div>
            <label className="block text-sm font-medium text-muted-foreground dark:text-muted-foreground mb-2">
              API Token
            </label>
            <div className="relative">
              <Input
                type={showToken ? 'text' : 'password'}
                value={formData.api_token}
                onChange={(e) => handleInputChange('api_token', e.target.value)}
                placeholder="Enter your Jira API Token"
                className={`w-full px-4 py-3 pr-12 rounded-xl border ${
                  validationErrors.api_token
                    ? 'border-red-300 dark:border-red-600'
                    : 'border-border/60 dark:border-border/60'
                } bg-background/80 text-foreground dark:text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-saramsa-brand/30 focus:border-saramsa-brand/40`}
              />
              <Button
                type="button"
                onClick={() => setShowToken(!showToken)}
                variant="ghost"
                size="icon"
                className="absolute right-2 top-1/2 -translate-y-1/2 h-8 w-8 hover:bg-accent/60 dark:hover:bg-accent/60"
              >
                {showToken ? (
                  <EyeOff className="w-4 h-4 text-muted-foreground" />
                ) : (
                  <Eye className="w-4 h-4 text-muted-foreground" />
                )}
              </Button>
            </div>
            {validationErrors.api_token && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                {validationErrors.api_token}
              </p>
            )}
            <div className="mt-2 p-3 bg-secondary/50 rounded-xl">
              <p className="text-sm text-foreground mb-2">
                <strong>Required Permissions:</strong>
              </p>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>- Browse projects and issues</li>
                <li>- Create and edit issues</li>
                <li>- View project details</li>
              </ul>
              <a
                href="https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 mt-2 text-sm text-muted-foreground hover:underline"
              >
                Learn how to create an API Token
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>

          {/* Security Notice */}
          <div className="bg-secondary/40 dark:bg-background/50 rounded-xl p-4">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-foreground dark:text-foreground mb-1">
                  Security & Privacy
                </h4>
                <ul className="text-sm text-muted-foreground dark:text-muted-foreground space-y-1">
                  <li>- Your API token is encrypted and stored securely</li>
                  <li>- We only access projects you explicitly import</li>
                  <li>- You can revoke access anytime from this page</li>
                  <li>- No data is shared with third parties</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              className="flex-1 h-12"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="saramsa"
              disabled={loading}
              className="flex-1 h-12"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Connecting...
                </>
              ) : (
                'Connect Jira'
              )}
            </Button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  );
}


