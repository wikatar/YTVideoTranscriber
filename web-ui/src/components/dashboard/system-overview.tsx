"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
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
  Zap,
  CheckCircle,
  XCircle,
  AlertCircle
} from "lucide-react";
import { apiClient, SystemStatus } from "@/lib/api";
import { toast } from "sonner";

interface SystemOverviewProps {
  status: SystemStatus | undefined;
}

export function SystemOverview({ status }: SystemOverviewProps) {
  const queryClient = useQueryClient();

  const startMonitoring = useMutation({
    mutationFn: apiClient.startMonitoring,
    onSuccess: () => {
      toast.success("Monitoring started successfully");
      queryClient.invalidateQueries({ queryKey: ['system-status'] });
    },
    onError: (error: any) => {
      toast.error(`Failed to start monitoring: ${error.response?.data?.detail || error.message}`);
    },
  });

  const stopMonitoring = useMutation({
    mutationFn: apiClient.stopMonitoring,
    onSuccess: () => {
      toast.success("Monitoring stopped successfully");
      queryClient.invalidateQueries({ queryKey: ['system-status'] });
    },
    onError: (error: any) => {
      toast.error(`Failed to stop monitoring: ${error.response?.data?.detail || error.message}`);
    },
  });

  const runCycle = useMutation({
    mutationFn: apiClient.runCycle,
    onSuccess: () => {
      toast.success("Processing cycle started");
      queryClient.invalidateQueries({ queryKey: ['system-status'] });
    },
    onError: (error: any) => {
      toast.error(`Failed to start cycle: ${error.response?.data?.detail || error.message}`);
    },
  });

  if (!status) return null;

  const completionRate = status.videos.total > 0 
    ? (status.videos.completed / status.videos.total) * 100 
    : 0;

  return (
    <div className="space-y-6">
      {/* System Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Status</CardTitle>
            {status.is_running ? (
              <CheckCircle className="h-4 w-4 text-green-600" />
            ) : (
              <XCircle className="h-4 w-4 text-red-600" />
            )}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {status.is_running ? "Running" : "Stopped"}
            </div>
            <p className="text-xs text-muted-foreground">
              Monitoring {status.channels.active} channels
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Channels</CardTitle>
            <Youtube className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{status.channels.active}</div>
            <p className="text-xs text-muted-foreground">
              {status.channels.total} total channels
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Videos Processed</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{status.videos.completed}</div>
            <p className="text-xs text-muted-foreground">
              {status.videos.pending} pending, {status.videos.failed} failed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Storage Saved</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {status.storage.estimated_storage_saved_mb?.toFixed(0) || 0} MB
            </div>
            <p className="text-xs text-muted-foreground">
              With optimization enabled
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Processing Progress */}
      <Card>
        <CardHeader>
          <CardTitle>Processing Overview</CardTitle>
          <CardDescription>
            Current status of video processing pipeline
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Completion Rate</span>
              <span>{completionRate.toFixed(1)}%</span>
            </div>
            <Progress value={completionRate} className="h-2" />
          </div>
          
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-green-600">{status.videos.completed}</div>
              <div className="text-xs text-muted-foreground">Completed</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-yellow-600">{status.videos.pending}</div>
              <div className="text-xs text-muted-foreground">Pending</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-red-600">{status.videos.failed}</div>
              <div className="text-xs text-muted-foreground">Failed</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Metrics */}
      {status.performance && (
        <Card>
          <CardHeader>
            <CardTitle>Performance Metrics</CardTitle>
            <CardDescription>
              System performance and processing statistics
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center space-x-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <div>
                  <div className="text-sm font-medium">Avg Processing Time</div>
                  <div className="text-2xl font-bold">
                    {status.performance.average_processing_time?.toFixed(1) || 0}s
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
                <div>
                  <div className="text-sm font-medium">Processing Rate</div>
                  <div className="text-2xl font-bold">
                    {status.performance.videos_per_hour?.toFixed(1) || 0}/hr
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Storage Optimization Status */}
      <Card>
        <CardHeader>
          <CardTitle>Storage Optimization</CardTitle>
          <CardDescription>
            Current optimization settings and savings
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm">Immediate Cleanup</span>
                <Badge variant={status.storage.immediate_cleanup ? "default" : "secondary"}>
                  {status.storage.immediate_cleanup ? "Enabled" : "Disabled"}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Audio-Only Downloads</span>
                <Badge variant={status.storage.audio_only_downloads ? "default" : "secondary"}>
                  {status.storage.audio_only_downloads ? "Enabled" : "Disabled"}
                </Badge>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm">Format</span>
                <Badge variant="outline">
                  {status.storage.compressed_format || "Standard"}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Storage Saved</span>
                <Badge variant="default">
                  {status.storage.estimated_storage_saved_mb?.toFixed(0) || 0} MB
                </Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Control Panel */}
      <Card>
        <CardHeader>
          <CardTitle>System Controls</CardTitle>
          <CardDescription>
            Start, stop, or run monitoring cycles
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Button
              onClick={() => status.is_running ? stopMonitoring.mutate() : startMonitoring.mutate()}
              disabled={startMonitoring.isPending || stopMonitoring.isPending}
              variant={status.is_running ? "destructive" : "default"}
            >
              {startMonitoring.isPending || stopMonitoring.isPending ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : status.is_running ? (
                <Pause className="h-4 w-4 mr-2" />
              ) : (
                <Play className="h-4 w-4 mr-2" />
              )}
              {status.is_running ? "Stop Monitoring" : "Start Monitoring"}
            </Button>
            
            <Button
              onClick={() => runCycle.mutate()}
              disabled={runCycle.isPending}
              variant="outline"
            >
              {runCycle.isPending ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4 mr-2" />
              )}
              Run Cycle
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
