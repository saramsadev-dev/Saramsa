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
      <div className="bg-card/80 rounded-2xl shadow-sm border border-border/60 p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">Action Items</h3>
        <div className="text-center py-8">
          <p className="text-muted-foreground">
            No action items available.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-card/80 rounded-2xl shadow-sm border border-border/60 p-6">
      <h3 className="text-lg font-semibold text-foreground mb-4">Action Items</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Feature Requests */}
        {actionItems.featurerequests && actionItems.featurerequests.length > 0 && (
          <div className="bg-secondary/40 p-6 rounded-xl border border-border/60">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-background/80 rounded-xl border border-border/60">
                <CheckCircle className="w-5 h-5 text-saramsa-brand" />
              </div>
              <div>
                <h4 className="font-semibold text-foreground">Feature Requests</h4>
                <p className="text-sm text-muted-foreground">
                  {actionItems.featurerequests.length} items
                </p>
              </div>
            </div>
            <ul className="space-y-3">
              {actionItems.featurerequests.map((item, index) => (
                <li key={index} className="text-sm">
                  <div className="bg-card/80 p-3 rounded-xl border border-border/60">
                    <span className="font-medium text-foreground block mb-1">
                      {item.feature}
                    </span>
                    <span className="text-muted-foreground">
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
          <div className="bg-secondary/40 p-6 rounded-xl border border-border/60">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-background/80 rounded-xl border border-border/60">
                <AlertCircle className="w-5 h-5 text-saramsa-gradient-to" />
              </div>
              <div>
                <h4 className="font-semibold text-foreground">Bugs to Fix</h4>
                <p className="text-sm text-muted-foreground">
                  {actionItems.bugs.length} items
                </p>
              </div>
            </div>
            <ul className="space-y-3">
              {actionItems.bugs.map((item, index) => (
                <li key={index} className="text-sm">
                  <div className="bg-card/80 p-3 rounded-xl border border-border/60">
                    <span className="font-medium text-foreground block mb-1">
                      {item.feature}
                    </span>
                    <span className="text-muted-foreground">
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
          <div className="bg-secondary/40 p-6 rounded-xl border border-border/60">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-background/80 rounded-xl border border-border/60">
                <Clock className="w-5 h-5 text-muted-foreground" />
              </div>
              <div>
                <h4 className="font-semibold text-foreground">Change Requests</h4>
                <p className="text-sm text-muted-foreground">
                  {actionItems.changerequests.length} items
                </p>
              </div>
            </div>
            <ul className="space-y-3">
              {actionItems.changerequests.map((item, index) => (
                <li key={index} className="text-sm">
                  <div className="bg-card/80 p-3 rounded-xl border border-border/60">
                    <span className="font-medium text-foreground block mb-1">
                      {item.feature}
                    </span>
                    <span className="text-muted-foreground">
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


