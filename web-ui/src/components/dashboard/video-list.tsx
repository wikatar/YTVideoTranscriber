"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { 
  Play, 
  FileText, 
  Clock, 
  ExternalLink,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader,
  Download,
  Eye
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";
import { formatDistanceToNow } from "date-fns";
import { TranscriptionViewer } from "./transcription-viewer";

export function VideoList() {
  const [selectedVideoId, setSelectedVideoId] = useState<string | null>(null);
  const [processVideoUrl, setProcessVideoUrl] = useState("");
  const queryClient = useQueryClient();

  const { data: allVideos, isLoading: allLoading } = useQuery({
    queryKey: ['videos', 'all'],
    queryFn: () => apiClient.getVideos(100),
  });

  const { data: pendingVideos, isLoading: pendingLoading } = useQuery({
    queryKey: ['videos', 'pending'],
    queryFn: () => apiClient.getVideos(50, 'pending'),
  });

  const { data: completedVideos, isLoading: completedLoading } = useQuery({
    queryKey: ['videos', 'completed'],
    queryFn: () => apiClient.getVideos(50, 'completed'),
  });

  const processVideoMutation = useMutation({
    mutationFn: apiClient.processVideo,
    onSuccess: () => {
      toast.success("Video processing started");
      setProcessVideoUrl("");
      queryClient.invalidateQueries({ queryKey: ['videos'] });
    },
    onError: (error: any) => {
      toast.error(`Failed to process video: ${error.response?.data?.detail || error.message}`);
    },
  });

  const handleProcessVideo = (e: React.FormEvent) => {
    e.preventDefault();
    if (!processVideoUrl.trim()) return;
    
    if (!processVideoUrl.includes('youtube.com/watch')) {
      toast.error("Please enter a valid YouTube video URL");
      return;
    }
    
    processVideoMutation.mutate(processVideoUrl.trim());
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-gray-600" />;
      case 'downloading':
      case 'transcribing':
        return <Loader className="h-4 w-4 text-blue-600 animate-spin" />;
      default:
        return <AlertCircle className="h-4 w-4 text-yellow-600" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      completed: "default",
      failed: "destructive",
      pending: "secondary",
      downloading: "outline",
      transcribing: "outline",
    };
    
    return (
      <Badge variant={variants[status] || "outline"} className="flex items-center gap-1">
        {getStatusIcon(status)}
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return "Unknown";
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const VideoTable = ({ videos, loading }: { videos: any[], loading: boolean }) => (
    <div className="rounded-md border">
      {loading ? (
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="h-6 w-6 animate-spin mr-2" />
          Loading videos...
        </div>
      ) : videos.length > 0 ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Video</TableHead>
              <TableHead>Channel</TableHead>
              <TableHead>Duration</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Upload Date</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {videos.map((video) => (
              <TableRow key={video.id}>
                <TableCell>
                  <div className="space-y-1 max-w-xs">
                    <div className="font-medium line-clamp-2">{video.title}</div>
                    <div className="text-xs text-muted-foreground">
                      ID: {video.video_id}
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="text-sm">{video.channel_name}</div>
                </TableCell>
                <TableCell>
                  <div className="text-sm">{formatDuration(video.duration_seconds)}</div>
                </TableCell>
                <TableCell>
                  {getStatusBadge(video.status)}
                </TableCell>
                <TableCell>
                  <div className="text-sm">
                    {video.upload_date ? (
                      <>
                        <div>{formatDistanceToNow(new Date(video.upload_date))} ago</div>
                        <div className="text-xs text-muted-foreground">
                          {new Date(video.upload_date).toLocaleDateString()}
                        </div>
                      </>
                    ) : (
                      <span className="text-muted-foreground">Unknown</span>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => window.open(video.url, '_blank')}
                    >
                      <ExternalLink className="h-3 w-3 mr-1" />
                      View
                    </Button>
                    {video.status === 'completed' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSelectedVideoId(video.video_id)}
                      >
                        <Eye className="h-3 w-3 mr-1" />
                        Transcript
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : (
        <div className="text-center py-8">
          <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-2">No videos found</h3>
          <p className="text-muted-foreground">
            Videos will appear here once they are discovered and processed
          </p>
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Process Single Video */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Play className="h-5 w-5" />
            Process Single Video
          </CardTitle>
          <CardDescription>
            Process a specific YouTube video immediately
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleProcessVideo} className="flex gap-4">
            <Input
              placeholder="https://www.youtube.com/watch?v=..."
              value={processVideoUrl}
              onChange={(e) => setProcessVideoUrl(e.target.value)}
              className="flex-1"
            />
            <Button 
              type="submit" 
              disabled={processVideoMutation.isPending || !processVideoUrl.trim()}
            >
              {processVideoMutation.isPending ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Play className="h-4 w-4 mr-2" />
              )}
              Process
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Videos Tabs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Videos
          </CardTitle>
          <CardDescription>
            View and manage processed videos
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="all" className="space-y-4">
            <TabsList>
              <TabsTrigger value="all">
                All Videos ({allVideos?.length || 0})
              </TabsTrigger>
              <TabsTrigger value="pending">
                Pending ({pendingVideos?.length || 0})
              </TabsTrigger>
              <TabsTrigger value="completed">
                Completed ({completedVideos?.length || 0})
              </TabsTrigger>
            </TabsList>

            <TabsContent value="all">
              <VideoTable videos={allVideos || []} loading={allLoading} />
            </TabsContent>

            <TabsContent value="pending">
              <VideoTable videos={pendingVideos || []} loading={pendingLoading} />
            </TabsContent>

            <TabsContent value="completed">
              <VideoTable videos={completedVideos || []} loading={completedLoading} />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Transcription Viewer Modal */}
      {selectedVideoId && (
        <TranscriptionViewer
          videoId={selectedVideoId}
          onClose={() => setSelectedVideoId(null)}
        />
      )}
    </div>
  );
}
