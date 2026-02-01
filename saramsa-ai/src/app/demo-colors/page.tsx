'use client';

import { StatusDurationExamples } from '@/components/ui/StatusDurationDisplay';
import { MetricsCards } from '@/components/ui/dashboard/MetricsCards';
import { AnalysisLoading } from '@/components/ui/AnalysisLoading';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { useState } from 'react';

export default function DemoColorsPage() {
  const [activeTab, setActiveTab] = useState('status');

  // Demo metrics with colorful status and duration
  const demoMetrics = [
    {
      title: "Processing Speed",
      value: "2.3s",
      color: "purple" as const,
      description: "Average analysis duration",
      status: "success" as const,
      duration: "Fast"
    },
    {
      title: "Success Rate",
      value: "98.5%",
      color: "green" as const,
      description: "Successful operations",
      status: "success" as const,
      duration: "Real-time"
    },
    {
      title: "Error Rate",
      value: "1.5%",
      color: "red" as const,
      description: "Failed operations",
      status: "failure" as const,
      duration: "0.8s avg"
    },
    {
      title: "Queue Length",
      value: "12",
      color: "orange" as const,
      description: "Pending tasks",
      status: "processing" as const,
      duration: "5m est"
    },
    {
      title: "Active Users",
      value: "1,234",
      color: "teal" as const,
      description: "Currently online",
      status: "success" as const,
      duration: "Live"
    },
    {
      title: "System Load",
      value: "45%",
      color: "blue" as const,
      description: "CPU utilization",
      status: "pending" as const,
      duration: "Monitoring"
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            🎨 Colorful UI Components Demo
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400">
            Showcasing enhanced colorful status indicators, duration displays, and triggers
          </p>
        </div>

        {/* Navigation Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <div className="flex justify-center">
            <TabsList className="grid w-full max-w-md grid-cols-4">
              <TabsTrigger value="status">Status</TabsTrigger>
              <TabsTrigger value="metrics">Metrics</TabsTrigger>
              <TabsTrigger value="loading">Loading</TabsTrigger>
              <TabsTrigger value="triggers">Triggers</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="status">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-8">
              <StatusDurationExamples />
            </div>
          </TabsContent>

          <TabsContent value="metrics">
            <div className="space-y-8">
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-8">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
                  Enhanced Metrics Cards
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  Colorful metrics with status indicators and duration displays
                </p>
                <MetricsCards metrics={demoMetrics} />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="loading">
            <div className="space-y-8">
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-8">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
                  Loading States
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Processing</h3>
                    <AnalysisLoading status="processing" message="Analyzing feedback data..." />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Pending</h3>
                    <AnalysisLoading status="pending" />
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="triggers">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-8">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
                Enhanced Tab Triggers
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Colorful tab triggers with gradients and hover effects
              </p>
              
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                    Dashboard Navigation
                  </h3>
                  <Tabs value="dashboard" onValueChange={() => {}}>
                    <TabsList>
                      <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
                      <TabsTrigger value="analytics">Analytics</TabsTrigger>
                      <TabsTrigger value="reports">Reports</TabsTrigger>
                      <TabsTrigger value="settings">Settings</TabsTrigger>
                    </TabsList>
                  </Tabs>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                    Analysis Views
                  </h3>
                  <Tabs value="sentiment" onValueChange={() => {}}>
                    <TabsList>
                      <TabsTrigger value="sentiment">Sentiment</TabsTrigger>
                      <TabsTrigger value="features">Features</TabsTrigger>
                      <TabsTrigger value="keywords">Keywords</TabsTrigger>
                      <TabsTrigger value="trends">Trends</TabsTrigger>
                    </TabsList>
                  </Tabs>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                    Project Management
                  </h3>
                  <Tabs value="active" onValueChange={() => {}}>
                    <TabsList>
                      <TabsTrigger value="active">Active</TabsTrigger>
                      <TabsTrigger value="completed">Completed</TabsTrigger>
                      <TabsTrigger value="archived">Archived</TabsTrigger>
                    </TabsList>
                  </Tabs>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        {/* Color Palette Reference */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-8">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
            Color Palette Reference
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {[
              { name: 'Success', color: 'bg-green-500', text: 'Green for success states' },
              { name: 'Failure', color: 'bg-red-500', text: 'Red for error states' },
              { name: 'Processing', color: 'bg-purple-500', text: 'Purple for active processing' },
              { name: 'Pending', color: 'bg-blue-500', text: 'Blue for pending states' },
              { name: 'Warning', color: 'bg-orange-500', text: 'Orange for warnings' },
              { name: 'Info', color: 'bg-teal-500', text: 'Teal for information' },
              { name: 'Primary', color: 'bg-indigo-500', text: 'Indigo for primary actions' },
              { name: 'Secondary', color: 'bg-gray-500', text: 'Gray for secondary elements' }
            ].map((item) => (
              <div key={item.name} className="text-center">
                <div className={`${item.color} w-full h-16 rounded-lg mb-2 shadow-md`}></div>
                <h4 className="font-medium text-gray-900 dark:text-white">{item.name}</h4>
                <p className="text-xs text-gray-500 dark:text-gray-400">{item.text}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Implementation Notes */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-2xl border border-blue-200 dark:border-blue-700 p-8">
          <h2 className="text-2xl font-bold text-blue-900 dark:text-blue-300 mb-4">
            🚀 Implementation Highlights
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-semibold text-blue-800 dark:text-blue-300 mb-3">
                Enhanced Features
              </h3>
              <ul className="space-y-2 text-blue-700 dark:text-blue-400">
                <li>✅ Colorful status indicators (success = green, failure = red)</li>
                <li>⏱️ Duration displays with colorful backgrounds</li>
                <li>🎨 Gradient backgrounds and borders</li>
                <li>✨ Smooth animations and transitions</li>
                <li>🌙 Dark mode support for all colors</li>
                <li>📱 Responsive design across all components</li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-blue-800 dark:text-blue-300 mb-3">
                Components Updated
              </h3>
              <ul className="space-y-2 text-blue-700 dark:text-blue-400">
                <li>📊 MetricsCards - Enhanced with status & duration</li>
                <li>⚡ AnalysisLoading - Colorful loading states</li>
                <li>🏷️ StatusDurationDisplay - New comprehensive component</li>
                <li>📑 Tabs - Enhanced trigger styling</li>
                <li>✅ User Stories Editor - Better status colors</li>
                <li>🔧 Work Item Tests - Improved result displays</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}