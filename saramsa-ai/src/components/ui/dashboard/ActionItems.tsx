'use client';

import { CheckCircle, AlertCircle, Clock } from 'lucide-react';

interface ActionItem {
  feature: string;
  request?: string;
  issue?: string;
}

interface ActionItems {
  featurerequests?: ActionItem[];
  bugs?: ActionItem[];
  changerequests?: ActionItem[];
}

interface ActionItemsProps {
  actionItems: ActionItems;
}

export function ActionItems({ actionItems }: ActionItemsProps) {
  if (!actionItems || (!actionItems.featurerequests?.length && !actionItems.bugs?.length && !actionItems.changerequests?.length)) {
    return (
      <div className="bg-card/90 dark:bg-card/95 rounded-2xl shadow-xl border border-border/60 dark:border-border/60 p-6">
        <h3 className="text-lg font-semibold text-foreground dark:text-foreground mb-4">Action Items</h3>
        <div className="text-center py-8">
          <p className="text-muted-foreground dark:text-muted-foreground">
            No action items available.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-card/90 dark:bg-card/95 rounded-2xl shadow-xl border border-border/60 dark:border-border/60 p-6">
      <h3 className="text-lg font-semibold text-foreground dark:text-foreground mb-4">Action Items</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Feature Requests */}
        {actionItems.featurerequests && actionItems.featurerequests.length > 0 && (
          <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 p-6 rounded-xl border border-green-200 dark:border-green-800">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-green-100 dark:bg-green-900/40 rounded-xl">
                <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <h4 className="font-semibold text-green-800 dark:text-green-300">Feature Requests</h4>
                <p className="text-sm text-green-600 dark:text-green-400">
                  {actionItems.featurerequests.length} items
                </p>
              </div>
            </div>
            <ul className="space-y-3">
              {actionItems.featurerequests.map((item, index) => (
                <li key={index} className="text-sm">
                  <div className="bg-card/90 dark:bg-card/95 p-3 rounded-xl border border-green-200 dark:border-green-800">
                    <span className="font-medium text-green-800 dark:text-green-300 block mb-1">
                      {item.feature}
                    </span>
                    <span className="text-muted-foreground dark:text-muted-foreground">
                      {item.request}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {/* Bugs */}
        {actionItems.bugs && actionItems.bugs.length > 0 && (
          <div className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 p-6 rounded-xl border border-red-200 dark:border-red-800">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-red-100 dark:bg-red-900/40 rounded-xl">
                <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
              </div>
              <div>
                <h4 className="font-semibold text-red-800 dark:text-red-300">Bugs to Fix</h4>
                <p className="text-sm text-red-600 dark:text-red-400">
                  {actionItems.bugs.length} items
                </p>
              </div>
            </div>
            <ul className="space-y-3">
              {actionItems.bugs.map((item, index) => (
                <li key={index} className="text-sm">
                  <div className="bg-card/90 dark:bg-card/95 p-3 rounded-xl border border-red-200 dark:border-red-800">
                    <span className="font-medium text-red-800 dark:text-red-300 block mb-1">
                      {item.feature}
                    </span>
                    <span className="text-muted-foreground dark:text-muted-foreground">
                      {item.issue}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {/* Change Requests */}
        {actionItems.changerequests && actionItems.changerequests.length > 0 && (
          <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 p-6 rounded-xl border border-yellow-200 dark:border-yellow-800">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-yellow-100 dark:bg-yellow-900/40 rounded-xl">
                <Clock className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
              </div>
              <div>
                <h4 className="font-semibold text-yellow-800 dark:text-yellow-300">Change Requests</h4>
                <p className="text-sm text-yellow-600 dark:text-yellow-400">
                  {actionItems.changerequests.length} items
                </p>
              </div>
            </div>
            <ul className="space-y-3">
              {actionItems.changerequests.map((item, index) => (
                <li key={index} className="text-sm">
                  <div className="bg-card/90 dark:bg-card/95 p-3 rounded-xl border border-yellow-200 dark:border-yellow-800">
                    <span className="font-medium text-yellow-800 dark:text-yellow-300 block mb-1">
                      {item.feature}
                    </span>
                    <span className="text-muted-foreground dark:text-muted-foreground">
                      {item.request}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
