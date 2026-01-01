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
                return 'text-blue-600';
            case 'processing':
                return 'text-indigo-600';
            case 'failure':
                return 'text-red-600';
            default:
                return 'text-gray-600';
        }
    };

    return (
        <div className="flex flex-col items-center justify-center py-12 px-4">
            <div className="relative">
                <Loader2 className={`h-12 w-12 animate-spin ${getStatusColor()}`} />
                <div className="absolute inset-0 flex items-center justify-center">
                    <div className={`h-8 w-8 rounded-full ${status === 'processing' ? 'bg-indigo-100 animate-pulse' : ''}`} />
                </div>
            </div>

            <div className="mt-6 text-center">
                <h3 className={`text-lg font-semibold ${getStatusColor()}`}>
                    {getStatusMessage()}
                </h3>

                {status === 'processing' && (
                    <div className="mt-4 space-y-2">
                        <p className="text-sm text-gray-600">
                            This may take a few moments...
                        </p>
                        <div className="flex items-center justify-center space-x-2">
                            <div className="h-2 w-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                            <div className="h-2 w-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                            <div className="h-2 w-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                        </div>
                    </div>
                )}
            </div>

            {status === 'processing' && (
                <div className="mt-6 w-full max-w-md">
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 animate-pulse" style={{ width: '60%' }} />
                    </div>
                    <p className="text-xs text-gray-500 mt-2 text-center">
                        Processing AI analysis...
                    </p>
                </div>
            )}
        </div>
    );
};
