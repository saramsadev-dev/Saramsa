'use client';

import { useState } from 'react';
import { useDispatch } from 'react-redux';
import type { AppDispatch } from '@/store/store';
import { createJiraIntegration } from '@/store/features/integrations/integrationsSlice';
import { motion } from 'framer-motion';
import { X, ExternalLink, Eye, EyeOff, Loader2, CheckCircle, AlertCircle } from 'lucide-react';

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
        className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold">J</span>
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Connect Jira
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Add your Jira Cloud instance to import projects
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Error Display */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4"
            >
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-500" />
                <span className="text-red-700 dark:text-red-300">{error}</span>
              </div>
            </motion.div>
          )}

          {/* Jira Domain */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Jira Domain
            </label>
            <div className="flex items-center">
              <span className="text-gray-500 dark:text-gray-400 text-sm mr-2">https://</span>
              <input
                type="text"
                value={formData.domain}
                onChange={(e) => handleInputChange('domain', e.target.value)}
                placeholder="yourcompany"
                className={`flex-1 px-4 py-3 rounded-lg border ${
                  validationErrors.domain
                    ? 'border-red-300 dark:border-red-600'
                    : 'border-gray-300 dark:border-gray-600'
                } bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
              />
              <span className="text-gray-500 dark:text-gray-400 text-sm ml-2">.atlassian.net</span>
            </div>
            {validationErrors.domain && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                {validationErrors.domain}
              </p>
            )}
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Your Jira Cloud domain (without https:// or .atlassian.net)
            </p>
          </div>

          {/* Email */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Email Address
            </label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              placeholder="your.email@company.com"
              className={`w-full px-4 py-3 rounded-lg border ${
                validationErrors.email
                  ? 'border-red-300 dark:border-red-600'
                  : 'border-gray-300 dark:border-gray-600'
              } bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
            />
            {validationErrors.email && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                {validationErrors.email}
              </p>
            )}
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              The email address associated with your Jira account
            </p>
          </div>

          {/* API Token */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              API Token
            </label>
            <div className="relative">
              <input
                type={showToken ? 'text' : 'password'}
                value={formData.api_token}
                onChange={(e) => handleInputChange('api_token', e.target.value)}
                placeholder="Enter your Jira API Token"
                className={`w-full px-4 py-3 pr-12 rounded-lg border ${
                  validationErrors.api_token
                    ? 'border-red-300 dark:border-red-600'
                    : 'border-gray-300 dark:border-gray-600'
                } bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
              />
              <button
                type="button"
                onClick={() => setShowToken(!showToken)}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
              >
                {showToken ? (
                  <EyeOff className="w-4 h-4 text-gray-400" />
                ) : (
                  <Eye className="w-4 h-4 text-gray-400" />
                )}
              </button>
            </div>
            {validationErrors.api_token && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                {validationErrors.api_token}
              </p>
            )}
            <div className="mt-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <p className="text-sm text-blue-700 dark:text-blue-300 mb-2">
                <strong>Required Permissions:</strong>
              </p>
              <ul className="text-sm text-blue-600 dark:text-blue-400 space-y-1">
                <li>• Browse projects and issues</li>
                <li>• Create and edit issues</li>
                <li>• View project details</li>
              </ul>
              <a
                href="https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 mt-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
              >
                Learn how to create an API Token
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>

          {/* Security Notice */}
          <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-1">
                  Security & Privacy
                </h4>
                <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                  <li>• Your API token is encrypted and stored securely</li>
                  <li>• We only access projects you explicitly import</li>
                  <li>• You can revoke access anytime from this page</li>
                  <li>• No data is shared with third parties</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-500 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Connecting...
                </>
              ) : (
                'Connect Jira'
              )}
            </button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  );
}
