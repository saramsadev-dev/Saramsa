'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../card';
import { Button } from '../button';
import { Loader2 } from 'lucide-react';

export function CommentsAnalysisComponent() {
  const [isLoading, setIsLoading] = useState(true);
  const [comments, setComments] = useState<any[]>([]);

  useEffect(() => {
    // Simulate loading comments
    const timer = setTimeout(() => {
      setComments([
        { id: 1, text: 'This is a sample comment', sentiment: 'positive' },
        { id: 2, text: 'Another sample comment', sentiment: 'neutral' },
      ]);
      setIsLoading(false);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-saramsa-brand" />
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl font-bold">Comments Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {comments.length > 0 ? (
              comments.map((comment) => (
                <div key={comment.id} className="p-4 border rounded-lg">
                  <p className="text-gray-800 dark:text-gray-200">{comment.text}</p>
                  <div className="mt-2">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      comment.sentiment === 'positive' 
                        ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' 
                        : 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
                    }`}>
                      {comment.sentiment}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-gray-500 dark:text-gray-400">No comments found.</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
