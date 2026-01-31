import React from 'react';
import { Loader2 } from 'lucide-react';

interface AnalysisLoadingProps {
    status: 'idle' | 'pending' | 'processing' | 'success' | 'failure';
    message?: string;
}

export const AnalysisLoading: React.FC<AnalysisLoadingProps> = ({ status, message }) => {
    if (status === 'idle' || status === 'success') {
        return null;
    }

    const getStatusMessage = () => {
        switch (status) {
            case 'pending':
                return 'Starting analysis...';
            case 'processing':
                return message || 'Analyzing comments in background...';
            case 'failure':
                return 'Analysis failed';
            default:
                return 'Processing...';
        }
    };

    const getStatusColor = () => {
        switch (status) {
            case 'pending':
                return 'text-blue-600 dark:text-blue-400';
            case 'processing':
                return 'text-purple-600 dark:text-purple-400';
            case 'failure':
                return 'text-red-600 dark:text-red-400';
            default:
                return 'text-gray-600 dark:text-gray-400';
        }
    };

    const getStatusBgColor = () => {
        switch (status) {
            case 'pending':
                return 'bg-blue-100 dark:bg-blue-900/20';
            case 'processing':
                return 'bg-purple-100 dark:bg-purple-900/20';
            case 'failure':
                return 'bg-red-100 dark:bg-red-900/20';
            default:
                return 'bg-gray-100 dark:bg-gray-900/20';
        }
    };

    return (
        <div className="flex flex-col items-center justify-center py-12 px-4">
            <div className="relative">
                <Loader2 className={`h-12 w-12 animate-spin ${getStatusColor()}`} />
                <div className="absolute inset-0 flex items-center justify-center">
                    <div className={`h-8 w-8 rounded-full ${status === 'processing' ? 'bg-purple-100 dark:bg-purple-900/20 animate-pulse' : ''}`} />
                </div>
            </div>

            <div className="mt-6 text-center">
                <div className={`inline-block px-4 py-2 rounded-full ${getStatusBgColor()} mb-2`}>
                    <h3 className={`text-lg font-semibold ${getStatusColor()}`}>
                        {getStatusMessage()}
                    </h3>
                </div>

                {status === 'processing' && (
                    <div className="mt-4 space-y-2">
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                            This may take a few moments...
                        </p>
                        <div className="flex items-center justify-center space-x-2">
                            <div className="h-2 w-2 bg-purple-600 dark:bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                            <div className="h-2 w-2 bg-purple-600 dark:bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                            <div className="h-2 w-2 bg-purple-600 dark:bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                        </div>
                    </div>
                )}
            </div>

            {status === 'processing' && (
                <div className="mt-6 w-full max-w-md">
                    <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-purple-500 to-pink-500 animate-pulse" style={{ width: '60%' }} />
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 text-center">
                        Processing AI analysis...
                    </p>
                </div>
            )}
        </div>
    );
};
