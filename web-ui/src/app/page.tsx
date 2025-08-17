"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { 
  Play, 
  Pause, 
  RefreshCw, 
  Database, 
  HardDrive, 
  Clock, 
  TrendingUp,
  Youtube,
  FileText,
  Users,
  Zap
} from "lucide-react";
import { SystemOverview } from "@/components/dashboard/system-overview";
import { ChannelManager } from "@/components/dashboard/channel-manager";
import { VideoList } from "@/components/dashboard/video-list";
import { SearchInterface } from "@/components/dashboard/search-interface";
import { StorageStatus } from "@/components/dashboard/storage-status";

export default function Dashboard() {
  const { data: status, isLoading, error } = useQuery({
    queryKey: ['system-status'],
    queryFn: apiClient.getStatus,
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading system status...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Alert className="max-w-md">
          <AlertDescription>
            Failed to connect to the transcription system. Make sure the API server is running on port 8000.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <Youtube className="h-8 w-8 text-red-600" />
                Video Transcription System
              </h1>
              <p className="text-gray-600 mt-1">
                Automated YouTube channel monitoring and transcription
              </p>
            </div>
            <div className="flex items-center gap-4">
              <Badge 
                variant={status?.is_running ? "default" : "secondary"}
                className="flex items-center gap-2"
              >
                {status?.is_running ? (
                  <>
                    <Play className="h-3 w-3" />
                    Running
                  </>
                ) : (
                  <>
                    <Pause className="h-3 w-3" />
                    Stopped
                  </>
                )}
              </Badge>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <Database className="h-4 w-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="channels" className="flex items-center gap-2">
              <Youtube className="h-4 w-4" />
              Channels
            </TabsTrigger>
            <TabsTrigger value="videos" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Videos
            </TabsTrigger>
            <TabsTrigger value="search" className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Search & Analytics
            </TabsTrigger>
            <TabsTrigger value="storage" className="flex items-center gap-2">
              <HardDrive className="h-4 w-4" />
              Storage
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <SystemOverview status={status} />
          </TabsContent>

          <TabsContent value="channels">
            <ChannelManager />
          </TabsContent>

          <TabsContent value="videos">
            <VideoList />
          </TabsContent>

          <TabsContent value="search">
            <SearchInterface />
          </TabsContent>

          <TabsContent value="storage">
            <StorageStatus />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}