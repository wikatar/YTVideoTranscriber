"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { 
  HardDrive, 
  Trash2, 
  RefreshCw, 
  CheckCircle, 
  AlertTriangle,
  Zap,
  Database,
  FileText,
  Gauge
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";

export function StorageStatus() {
  const queryClient = useQueryClient();

  const { data: storageData, isLoading, error } = useQuery({
    queryKey: ['storage-status'],
    queryFn: apiClient.getStorageStatus,
  });

  const cleanupMutation = useMutation({
    mutationFn: (force: boolean = false) => apiClient.cleanupStorage(force),
    onSuccess: () => {
      toast.success("Storage cleanup completed");
      queryClient.invalidateQueries({ queryKey: ['storage-status'] });
    },
    onError: (error: any) => {
      toast.error(`Cleanup failed: ${error.response?.data?.detail || error.message}`);
    },
  });

  if (error) {
    return (
      <Alert>
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Failed to load storage information. Please check your connection to the API server.
        </AlertDescription>
      </Alert>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <RefreshCw className="h-6 w-6 animate-spin mr-2" />
        Loading storage information...
      </div>
    );
  }

  const tempStorage = storageData?.temporary_storage || {};
  const transcriptionFiles = storageData?.transcription_files || {};
  const totalTempSizeMB = tempStorage.total_size_mb || 0;
  const totalTranscriptionSizeMB = transcriptionFiles.size_mb || 0;

  // Calculate storage usage percentage (assuming 2GB limit for temp storage)
  const maxTempStorageGB = storageData?.max_temp_storage_gb || 2;
  const tempUsagePercent = (totalTempSizeMB / (maxTempStorageGB * 1024)) * 100;

  return (
    <div className="space-y-6">
      {/* Storage Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Temporary Storage</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalTempSizeMB.toFixed(1)} MB</div>
            <p className="text-xs text-muted-foreground">
              {tempStorage.total_files || 0} files
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Transcriptions</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalTranscriptionSizeMB.toFixed(1)} MB</div>
            <p className="text-xs text-muted-foreground">
              {transcriptionFiles.count || 0} files
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Optimization</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {storageData?.immediate_cleanup_enabled ? "ON" : "OFF"}
            </div>
            <p className="text-xs text-muted-foreground">
              Immediate cleanup
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Usage</CardTitle>
            <Gauge className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{tempUsagePercent.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              of {maxTempStorageGB}GB limit
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Storage Usage Progress */}
      <Card>
        <CardHeader>
          <CardTitle>Storage Usage</CardTitle>
          <CardDescription>
            Current storage usage and optimization status
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Temporary Storage Usage</span>
              <span>{tempUsagePercent.toFixed(1)}% of {maxTempStorageGB}GB</span>
            </div>
            <Progress 
              value={tempUsagePercent} 
              className={`h-2 ${tempUsagePercent > 80 ? 'bg-red-100' : tempUsagePercent > 60 ? 'bg-yellow-100' : 'bg-green-100'}`}
            />
            {tempUsagePercent > 80 && (
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  Temporary storage is getting full. Consider running cleanup or enabling optimization.
                </AlertDescription>
              </Alert>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600">{totalTempSizeMB.toFixed(1)} MB</div>
              <div className="text-xs text-muted-foreground">Temporary Files</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">{totalTranscriptionSizeMB.toFixed(1)} MB</div>
              <div className="text-xs text-muted-foreground">Transcription Files</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* File Type Breakdown */}
      {tempStorage.file_types && Object.keys(tempStorage.file_types).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>File Type Breakdown</CardTitle>
            <CardDescription>
              Breakdown of temporary files by type
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(tempStorage.file_types).map(([ext, info]: [string, any]) => (
                <div key={ext} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{ext || 'No extension'}</Badge>
                    <span className="text-sm">{info.count} files</span>
                  </div>
                  <div className="text-sm font-medium">
                    {info.size_mb.toFixed(1)} MB
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Optimization Status */}
      <Card>
        <CardHeader>
          <CardTitle>Optimization Settings</CardTitle>
          <CardDescription>
            Current storage optimization configuration
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">Immediate Cleanup</span>
                <Badge variant={storageData?.immediate_cleanup_enabled ? "default" : "secondary"}>
                  {storageData?.immediate_cleanup_enabled ? (
                    <>
                      <CheckCircle className="h-3 w-3 mr-1" />
                      Enabled
                    </>
                  ) : (
                    "Disabled"
                  )}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Keep Failed Files</span>
                <Badge variant={storageData?.keep_failed_files ? "secondary" : "default"}>
                  {storageData?.keep_failed_files ? "Yes" : "No"}
                </Badge>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">Max Temp Storage</span>
                <Badge variant="outline">
                  {maxTempStorageGB} GB
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Cleanup Needed</span>
                <Badge variant={tempStorage.cleanup_needed ? "destructive" : "default"}>
                  {tempStorage.cleanup_needed ? "Yes" : "No"}
                </Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Storage Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Storage Management</CardTitle>
          <CardDescription>
            Clean up temporary files and manage storage
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Button
              onClick={() => cleanupMutation.mutate(false)}
              disabled={cleanupMutation.isPending}
              variant="outline"
            >
              {cleanupMutation.isPending ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4 mr-2" />
              )}
              Smart Cleanup
            </Button>
            
            <Button
              onClick={() => cleanupMutation.mutate(true)}
              disabled={cleanupMutation.isPending}
              variant="destructive"
            >
              {cleanupMutation.isPending ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4 mr-2" />
              )}
              Emergency Cleanup
            </Button>
          </div>
          <div className="mt-4 text-sm text-muted-foreground">
            <p><strong>Smart Cleanup:</strong> Removes old temporary files based on age and usage patterns.</p>
            <p><strong>Emergency Cleanup:</strong> Removes ALL temporary files immediately. Use with caution.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
