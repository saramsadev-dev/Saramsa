'use client';

import { useState } from 'react';
import { useDispatch } from 'react-redux';
import type { AppDispatch } from '@/store/store';
import { createAzureIntegration } from '@/store/features/integrations/integrationsSlice';
import { motion } from 'framer-motion';
import { ExternalLink, Eye, EyeOff, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { BaseModal } from '@/components/ui/modals/BaseModal';

interface AzureIntegrationFormProps {
  onClose: () => void;
  onSuccess: () => void;
}

export function AzureIntegrationForm({ onClose, onSuccess }: AzureIntegrationFormProps) {
  const dispatch = useDispatch<AppDispatch>();
  const [formData, setFormData] = useState({
    organization: '',
    pat_token: '',
  });
  const [showToken, setShowToken] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<{ [key: string]: string }>({});

  const validateForm = () => {
    const errors: { [key: string]: string } = {};
    
    if (!formData.organization.trim()) {
      errors.organization = 'Organization name is required';
    }
    
    if (!formData.pat_token.trim()) {
      errors.pat_token = 'Personal Access Token is required';
    } else if (formData.pat_token.length < 20) {
      errors.pat_token = 'PAT seems too short. Please check your token.';
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
      await dispatch(createAzureIntegration({
        organization: formData.organization.trim(),
        pat_token: formData.pat_token.trim(),
      })).unwrap();
      
      onSuccess();
    } catch (err: any) {
      setError(err.message || 'Failed to connect to Azure DevOps');
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
    <BaseModal
      isOpen={true}
      onClose={onClose}
      size="md"
      className="max-h-[90vh] overflow-y-auto"
      icon={
        <div className="w-10 h-10 bg-gradient-to-br from-saramsa-gradient-from to-saramsa-gradient-to rounded-xl flex items-center justify-center">
          <span className="text-white font-bold">Az</span>
        </div>
      }
      title="Connect Azure DevOps"
      description="Add your Azure DevOps organization to import projects"
      footer={
        <div className="flex gap-3">
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
            form="azure-integration-form"
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
              'Connect Azure DevOps'
            )}
          </Button>
        </div>
      }
    >
      <form id="azure-integration-form" onSubmit={handleSubmit} className="space-y-6">
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

          {/* Organization Name */}
          <div>
            <label className="block text-sm font-medium text-muted-foreground dark:text-muted-foreground mb-2">
              Organization Name
            </label>
            <Input
              type="text"
              value={formData.organization}
              onChange={(e) => handleInputChange('organization', e.target.value)}
              placeholder="e.g., mycompany"
              className={`w-full px-4 py-3 rounded-xl border ${
                validationErrors.organization
                  ? 'border-red-300 dark:border-red-600'
                  : 'border-border/60 dark:border-border/60'
              } bg-background/80 text-foreground dark:text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-saramsa-brand/30 focus:border-saramsa-brand/40`}
            />
            {validationErrors.organization && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                {validationErrors.organization}
              </p>
            )}
            <p className="mt-1 text-sm text-muted-foreground dark:text-muted-foreground">
              Your Azure DevOps organization name (from https://dev.azure.com/yourorg)
            </p>
          </div>

          {/* Personal Access Token */}
          <div>
            <label className="block text-sm font-medium text-muted-foreground dark:text-muted-foreground mb-2">
              Personal Access Token (PAT)
            </label>
            <div className="relative">
              <Input
                type={showToken ? 'text' : 'password'}
                value={formData.pat_token}
                onChange={(e) => handleInputChange('pat_token', e.target.value)}
                placeholder="Enter your Azure DevOps PAT"
                className={`w-full px-4 py-3 pr-12 rounded-xl border ${
                  validationErrors.pat_token
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
            {validationErrors.pat_token && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                {validationErrors.pat_token}
              </p>
            )}
            <div className="mt-2 p-3 bg-secondary/50 rounded-xl">
              <p className="text-sm text-foreground mb-2">
                <strong>Required Permissions:</strong>
              </p>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>- Project and team (read)</li>
                <li>- Work items (read & write)</li>
                <li>- Code (read) - optional</li>
              </ul>
              <a
                href="https://docs.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 mt-2 text-sm text-muted-foreground hover:underline"
              >
                Learn how to create a PAT
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
                  <li>- Your PAT is encrypted and stored securely</li>
                  <li>- We only access projects you explicitly import</li>
                  <li>- You can revoke access anytime from this page</li>
                  <li>- No data is shared with third parties</li>
                </ul>
              </div>
            </div>
          </div>
      </form>
    </BaseModal>
  );
}


