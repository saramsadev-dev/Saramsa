"use client";

import { useEffect, useRef, useState } from "react";
import { Upload, Cloud, BarChart3, FileText, FolderOpen, Trash2 } from 'lucide-react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../card";
import { Button } from "../button";
import { Badge } from "../badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../tabs";
import { Input } from "../input";
import { Label } from "../label";

interface UploadPanelProps {
  dbProjectId: string;
  topFile: File | null;
  topError: string | null;
  loadedComments: string[] | null;
  topUploading: boolean;
  onFileSelect: (file: File | null) => void;
  onAnalyze: () => Promise<void>;
  onCloudConnect: () => void;
  isAnalyzing?: boolean;
}

export function UploadPanel({
  dbProjectId,
  topFile,
  topError,
  loadedComments,
  topUploading,
  onFileSelect,
  onAnalyze,
  onCloudConnect,
  isAnalyzing = false,
}: UploadPanelProps) {
  const [activeTab, setActiveTab] = useState("file");
  const [isConnected, setIsConnected] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const isCloudEnabled = false;

  useEffect(() => {
    if (!isCloudEnabled && activeTab === "cloud") {
      setActiveTab("file");
    }
  }, [activeTab, isCloudEnabled]);

  const handleTabChange = (value: string) => {
    if (!isCloudEnabled && value === "cloud") {
      return;
    }
    setActiveTab(value);
  };

  const handleConnectCloud = () => {
    setIsConnected(true);
    onCloudConnect();
  };

  const handleFileSelect = (file: File | null) => {
    onFileSelect(file);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);
    const file = event.dataTransfer.files?.[0] ?? null;
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    if (!isDragging) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);
  };

  const removeFile = () => {
    onFileSelect(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const canAnalyze =
    (activeTab === "file" && topFile) || (activeTab === "cloud" && isConnected);

  return (
    <Card className="bg-card/80 rounded-2xl border border-border/60 shadow-[0_24px_60px_-40px_rgba(15,23,42,0.6)]">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-xl text-foreground">
              Feedback Analysis
            </CardTitle>
            <CardDescription className="text-muted-foreground mt-1">
              {dbProjectId
                ? "Upload feedback data for the selected project to analyze sentiment and generate insights."
                : (() => {
                    const platform =
                      typeof window !== "undefined"
                        ? localStorage.getItem("selected_platform") || "azure"
                        : "azure";
                    return platform === "jira"
                      ? "Browse files to preview data. Select a Jira project whenever you're ready to analyze."
                      : "Browse files to preview data. Select an Azure DevOps project whenever you're ready to analyze.";
                  })()}
            </CardDescription>
            {!dbProjectId && (
              <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                {(() => {
                  const platform =
                    typeof window !== "undefined"
                      ? localStorage.getItem("selected_platform") || "azure"
                      : "azure";
                  return platform === "jira"
                    ? "We will create the project in Saramsa DB automatically when you pick a new Jira project."
                    : "We will create the project in Saramsa DB automatically when you pick a new Azure DevOps project.";
                })()}
              </p>
            )}
          </div>
          {dbProjectId && (
            <Badge
              variant="secondary"
              className="bg-secondary/70 text-foreground"
            >
              {dbProjectId}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Input Options */}
        <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
          <TabsList className="grid w-full max-w-md grid-cols-2 rounded-xl overflow-hidden border border-border/70 bg-secondary/60 p-0">
            <TabsTrigger
              value="file"
              className={`${
                activeTab === "file"
                  ? "bg-secondary/80 text-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-secondary/40"
              } rounded-none border-l border-border/60 first:border-l-0`}
            >
              <Upload className="w-4 h-4 mr-2" />
              Choose File
            </TabsTrigger>
            <TabsTrigger
              value="cloud"
              onClick={() => {
                if (isCloudEnabled) {
                  setActiveTab("cloud");
                }
              }}
              className={`${
                activeTab === "cloud"
                  ? "bg-secondary/80 text-foreground"
                  : "text-muted-foreground/60 cursor-not-allowed"
              } rounded-none border-l border-border/60 first:border-l-0`}
              aria-disabled={!isCloudEnabled}
            >
              <Cloud className="w-4 h-4 mr-2" />
              Connect Cloud
              {!isCloudEnabled && (
                <span className="ml-2 text-xs uppercase tracking-wide text-muted-foreground/70">
                  Coming soon
                </span>
              )}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="file" className="space-y-4 mt-6">
            <div className="space-y-4">
              {!topFile ? (
                <div
                  className={`border rounded-2xl p-6 sm:p-8 transition-colors bg-background/60 ${
                    isDragging ? "border-saramsa-brand/40 bg-secondary/60" : "border-border/70"
                  }`}
                  onClick={() => document.getElementById("file-upload")?.click()}
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      document.getElementById("file-upload")?.click();
                    }
                  }}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                    <div className="w-12 h-12 rounded-2xl bg-secondary/80 border border-border/60 flex items-center justify-center">
                      <Upload className="w-5 h-5 text-muted-foreground" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-foreground">
                        Drop a CSV or JSON file here
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Or click to browse from your device
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      className="border-border/70 hover:bg-accent/60"
                      onClick={(e) => {
                        e.stopPropagation();
                        document.getElementById("file-upload")?.click();
                      }}
                    >
                      <FolderOpen className="w-4 h-4" />
                      Browse
                    </Button>
                  </div>
                  <Input
                    id="file-upload"
                    type="file"
                    ref={fileInputRef}
                    accept=".csv,.json"
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (!f) return;
                      handleFileSelect(f);
                    }}
                    className="hidden"
                  />
                </div>
              ) : (
                <div className="flex flex-col sm:flex-row sm:items-center gap-3 p-4 bg-secondary/60 rounded-2xl border border-border/60">
                  <div className="w-10 h-10 rounded-xl bg-background/80 border border-border/60 flex items-center justify-center">
                    <FileText className="w-5 h-5 text-muted-foreground" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-foreground">
                      {topFile.name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {(topFile.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                  <Badge variant="secondary" className="bg-secondary/80 text-foreground">
                    Ready
                  </Badge>
                  <div className="flex items-center gap-2 sm:ml-auto">
                    <Button
                      onClick={onAnalyze}
                      disabled={topUploading || !canAnalyze}
                      className="bg-foreground text-background hover:bg-foreground/90 disabled:opacity-50 gap-2 px-4"
                    >
                      <BarChart3 className="w-4 h-4 shrink-0" />
                      <span>Analyze</span>
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      className="border-border/70 hover:bg-accent/60"
                      onClick={removeFile}
                      title="Remove file"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="cloud" className="space-y-4 mt-6">
            <div className="border border-border/60 rounded-2xl p-6 bg-card/60">
              <div className="flex items-center gap-4 mb-4">
                <Cloud className="w-8 h-8 text-saramsa-brand" />
                <div>
                  <h3 className="text-foreground font-medium">
                    Cloud Data Sources
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {isCloudEnabled
                      ? "Connect to your cloud storage or data platforms"
                      : "Cloud connections are coming soon."}
                  </p>
                </div>
              </div>

              {!isCloudEnabled ? (
                <div className="p-4 bg-secondary/60 rounded-lg text-sm text-muted-foreground dark:text-muted-foreground">
                  We're working on cloud integrations. Stay tuned!
                </div>
              ) : !isConnected ? (
                <div className="space-y-3">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <Button
                      variant="outline"
                      className="border-border/70 hover:bg-accent/60 justify-start"
                      onClick={handleConnectCloud}
                    >
                      <div className="w-5 h-5 rounded bg-saramsa-brand mr-2"></div>
                      Google Drive
                    </Button>
                    <Button
                      variant="outline"
                      className="border-border/70 hover:bg-accent/60 justify-start"
                      onClick={handleConnectCloud}
                    >
                      <div className="w-5 h-5 rounded bg-saramsa-brand mr-2"></div>
                      Dropbox
                    </Button>
                    <Button
                      variant="outline"
                      className="border-border/70 hover:bg-accent/60 justify-start"
                      onClick={handleConnectCloud}
                    >
                      <div className="w-5 h-5 rounded bg-saramsa-brand mr-2"></div>
                      OneDrive
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center gap-3 p-3 bg-secondary/60 rounded-lg">
                    <div className="w-5 h-5 rounded bg-saramsa-brand"></div>
                    <div className="flex-1">
                      <p className="text-sm text-foreground">
                        Google Drive Connected
                      </p>
                      <p className="text-xs text-muted-foreground">
                        feedback_data.xlsx
                      </p>
                    </div>
                    <Badge
                      variant="secondary"
                      className="bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300"
                    >
                      Connected
                    </Badge>
                  </div>

                  <Button
                    onClick={onAnalyze}
                    disabled={topUploading}
                    className="w-full bg-foreground text-background hover:bg-foreground/90 disabled:opacity-50"
                  >
                    <BarChart3 className="w-4 h-4 mr-2" />
                    {topUploading ? "Analyzing..." : "Analyze"}
                  </Button>
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>

      {/* Error Display */}
      {topError && (
        <div className="px-6 pb-6">
          <div className="p-3 bg-red-50/80 dark:bg-red-900/20 border border-red-200/70 dark:border-red-800/60 rounded-2xl">
            <p className="text-sm text-red-600 dark:text-red-400">{topError}</p>
          </div>
        </div>
      )}
    </Card>
  );
}

