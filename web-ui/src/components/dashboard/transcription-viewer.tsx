"use client";

import { useQuery } from "@tanstack/react-query";
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { 
  FileText, 
  Clock, 
  Users, 
  Globe, 
  Star,
  Copy,
  Download,
  RefreshCw
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";

interface TranscriptionViewerProps {
  videoId: string;
  onClose: () => void;
}

export function TranscriptionViewer({ videoId, onClose }: TranscriptionViewerProps) {
  const { data: transcription, isLoading, error } = useQuery({
    queryKey: ['transcription', videoId],
    queryFn: () => apiClient.getTranscription(videoId),
    enabled: !!videoId,
  });

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard");
  };

  const downloadTranscription = () => {
    if (!transcription) return;
    
    const content = transcription.segments
      .map(segment => {
        const timestamp = `[${formatTime(segment.start)}]`;
        const speaker = segment.speaker ? ` ${segment.speaker}:` : '';
        return `${timestamp}${speaker} ${segment.text}`;
      })
      .join('\n');
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transcription_${videoId}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    toast.success("Transcription downloaded");
  };

  return (
    <Dialog open={!!videoId} onOpenChange={() => onClose()}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Video Transcription
          </DialogTitle>
          <DialogDescription>
            Video ID: {videoId}
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin mr-2" />
            Loading transcription...
          </div>
        ) : error ? (
          <div className="text-center py-8">
            <p className="text-red-600">Failed to load transcription</p>
          </div>
        ) : transcription ? (
          <div className="flex-1 overflow-hidden flex flex-col space-y-4">
            {/* Metadata */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="flex items-center gap-2">
                <Globe className="h-4 w-4 text-muted-foreground" />
                <div>
                  <div className="text-sm font-medium">Language</div>
                  <Badge variant="outline">{transcription.language}</Badge>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <Star className="h-4 w-4 text-muted-foreground" />
                <div>
                  <div className="text-sm font-medium">Confidence</div>
                  <Badge variant="outline">
                    {(transcription.confidence_score * 100).toFixed(1)}%
                  </Badge>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <div>
                  <div className="text-sm font-medium">Words</div>
                  <Badge variant="outline">{transcription.word_count}</Badge>
                </div>
              </div>
              
              {transcription.speakers.has_speaker_info && (
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <div className="text-sm font-medium">Speakers</div>
                    <Badge variant="outline">{transcription.speaker_count}</Badge>
                  </div>
                </div>
              )}
            </div>

            <Separator />

            {/* Actions */}
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => copyToClipboard(transcription.full_text)}
              >
                <Copy className="h-4 w-4 mr-2" />
                Copy Text
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={downloadTranscription}
              >
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
            </div>

            {/* Transcription Content */}
            <div className="flex-1 overflow-auto">
              <div className="space-y-3">
                {transcription.segments.map((segment, index) => (
                  <div key={index} className="flex gap-3 p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors">
                    <div className="flex-shrink-0">
                      <Badge variant="outline" className="text-xs">
                        <Clock className="h-3 w-3 mr-1" />
                        {formatTime(segment.start)}
                      </Badge>
                    </div>
                    
                    {segment.speaker && (
                      <div className="flex-shrink-0">
                        <Badge variant="secondary" className="text-xs">
                          <Users className="h-3 w-3 mr-1" />
                          {segment.speaker}
                        </Badge>
                      </div>
                    )}
                    
                    <div className="flex-1 text-sm leading-relaxed">
                      {segment.text}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
