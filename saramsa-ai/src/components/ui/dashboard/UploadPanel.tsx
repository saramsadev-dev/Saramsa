"use client";

import { useEffect, useRef, useState } from "react";
import { Upload, Cloud, BarChart3, FileText, FolderOpen, Trash2 } from "lucide-react";
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
}: UploadPanelProps) {
  const [activeTab, setActiveTab] = useState("file");
  const [isConnected, setIsConnected] = useState(false);
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

  const removeFile = () => {
    onFileSelect(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const canAnalyze =
    (activeTab === "file" && topFile) || (activeTab === "cloud" && isConnected);

  return (
    <Card className="bg-card/80 rounded-3xl border border-border/60 shadow-[0_24px_60px_-40px_rgba(15,23,42,0.6)]">
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
          <TabsList className="grid w-full max-w-md grid-cols-2">
            <TabsTrigger
              value="file"
              className={`${
                activeTab === "file"
                  ? "bg-gradient-to-r from-saramsa-gradient-from to-saramsa-gradient-to text-white shadow-[0_10px_24px_-16px_rgba(230,3,235,0.65)]"
                  : "text-muted-foreground hover:text-foreground hover:bg-background/70"
              }`}
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
                  ? "bg-gradient-to-r from-saramsa-gradient-from to-saramsa-gradient-to text-white shadow-[0_10px_24px_-16px_rgba(230,3,235,0.65)]"
                  : "text-muted-foreground/70 cursor-not-allowed"
              }`}
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
            {/* Single Full-Width Upload Area */}
            <div className="space-y-4">
              {!topFile ? (
                <div 
                  className="border border-dashed border-border/70 rounded-2xl p-12 text-center hover:border-saramsa-brand/40 transition-colors cursor-pointer bg-background/60"
                  onClick={() => document.getElementById("file-upload")?.click()}
                >
                  <Upload className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
                  <div className="space-y-2">
                    <Label
                      htmlFor="file-upload"
                      className="text-foreground cursor-pointer hover:text-foreground/80 text-lg"
                    >
                      Choose a file to upload
                    </Label>
                    <p className="text-sm text-muted-foreground">
                      CSV and JSON files
                    </p>
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
                  <Button
                    variant="outline"
                    className="mt-6 border-border/70 hover:bg-accent/60"
                    onClick={(e) => {
                      e.stopPropagation();
                      document.getElementById("file-upload")?.click();
                    }}
                  >
                    <FolderOpen className="w-5 h-5" />
                  </Button>
                </div>
              ) : (
                <div className="flex flex-row items-center gap-3 p-4 bg-secondary/60 rounded-2xl border border-border/60">
                  <FileText className="w-8 h-8 text-saramsa-brand" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-foreground">
                      {topFile.name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {(topFile.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                  <Badge
                    variant="secondary"
                    className="bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300"
                  >
                    Ready
                  </Badge>
                  <Button
                    onClick={onAnalyze}
                    disabled={topUploading}
                    className="bg-gradient-to-r from-saramsa-gradient-from to-saramsa-gradient-to hover:from-saramsa-brand-hover hover:to-saramsa-gradient-to disabled:opacity-50 gap-2 px-4"
                    title={topUploading ? "Analyzing..." : "Analyze"}
                  >
                    <BarChart3 className="w-5 h-5 shrink-0" />
                    <span className="hidden sm:inline">{topUploading ? "Analyzing..." : "Analyze"}</span>
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    className="bg-red-500 hover:bg-red-600 text-white border-red-500 w-10 h-10 p-0"
                    onClick={removeFile}
                    title="Delete file"
                  >
                    <Trash2 className="w-5 h-5" />
                  </Button>
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
                <div className="p-4 bg-secondary/60 rounded-lg text-sm text-gray-600 dark:text-gray-300">
                  We’re working on cloud integrations. Stay tuned!
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
                    className="w-full bg-gradient-to-r from-saramsa-gradient-from to-saramsa-gradient-to hover:from-saramsa-brand-hover hover:to-saramsa-gradient-to disabled:opacity-50"
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
