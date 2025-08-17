"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
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
  Plus, 
  Youtube, 
  Calendar, 
  ExternalLink,
  RefreshCw,
  CheckCircle,
  Clock
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";
import { formatDistanceToNow } from "date-fns";

export function ChannelManager() {
  const [newChannelUrl, setNewChannelUrl] = useState("");
  const queryClient = useQueryClient();

  const { data: channels, isLoading, error } = useQuery({
    queryKey: ['channels'],
    queryFn: apiClient.getChannels,
  });

  const addChannelMutation = useMutation({
    mutationFn: apiClient.addChannel,
    onSuccess: () => {
      toast.success("Channel added successfully");
      setNewChannelUrl("");
      queryClient.invalidateQueries({ queryKey: ['channels'] });
      queryClient.invalidateQueries({ queryKey: ['system-status'] });
    },
    onError: (error: any) => {
      toast.error(`Failed to add channel: ${error.response?.data?.detail || error.message}`);
    },
  });

  const handleAddChannel = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newChannelUrl.trim()) return;
    
    if (!newChannelUrl.includes('youtube.com')) {
      toast.error("Please enter a valid YouTube channel URL");
      return;
    }
    
    addChannelMutation.mutate(newChannelUrl.trim());
  };

  if (error) {
    return (
      <Alert>
        <AlertDescription>
          Failed to load channels. Please check your connection to the API server.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Add Channel Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5" />
            Add New Channel
          </CardTitle>
          <CardDescription>
            Add a YouTube channel to monitor for new video uploads
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleAddChannel} className="flex gap-4">
            <Input
              placeholder="https://www.youtube.com/@channelname"
              value={newChannelUrl}
              onChange={(e) => setNewChannelUrl(e.target.value)}
              className="flex-1"
            />
            <Button 
              type="submit" 
              disabled={addChannelMutation.isPending || !newChannelUrl.trim()}
            >
              {addChannelMutation.isPending ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Plus className="h-4 w-4 mr-2" />
              )}
              Add Channel
            </Button>
          </form>
          <div className="mt-4 text-sm text-muted-foreground">
            <p className="font-medium mb-2">Supported URL formats:</p>
            <ul className="space-y-1 text-xs">
              <li>• https://www.youtube.com/@channelname</li>
              <li>• https://www.youtube.com/c/channelname</li>
              <li>• https://www.youtube.com/channel/UC...</li>
              <li>• https://www.youtube.com/user/username</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Channels List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Youtube className="h-5 w-5" />
            Monitored Channels ({channels?.length || 0})
          </CardTitle>
          <CardDescription>
            Channels currently being monitored for new uploads
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="h-6 w-6 animate-spin mr-2" />
              Loading channels...
            </div>
          ) : channels && channels.length > 0 ? (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Channel</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Last Checked</TableHead>
                    <TableHead>Added</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {channels.map((channel) => (
                    <TableRow key={channel.id}>
                      <TableCell>
                        <div className="space-y-1">
                          <div className="font-medium">{channel.channel_name}</div>
                          <div className="text-sm text-muted-foreground">
                            ID: {channel.channel_id}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge 
                          variant={channel.is_active ? "default" : "secondary"}
                          className="flex items-center gap-1 w-fit"
                        >
                          {channel.is_active ? (
                            <>
                              <CheckCircle className="h-3 w-3" />
                              Active
                            </>
                          ) : (
                            <>
                              <Clock className="h-3 w-3" />
                              Inactive
                            </>
                          )}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {channel.last_checked ? (
                            <>
                              <div>{formatDistanceToNow(new Date(channel.last_checked))} ago</div>
                              <div className="text-xs text-muted-foreground">
                                {new Date(channel.last_checked).toLocaleDateString()}
                              </div>
                            </>
                          ) : (
                            <span className="text-muted-foreground">Never</span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {channel.created_at ? (
                            <>
                              <div>{formatDistanceToNow(new Date(channel.created_at))} ago</div>
                              <div className="text-xs text-muted-foreground">
                                {new Date(channel.created_at).toLocaleDateString()}
                              </div>
                            </>
                          ) : (
                            <span className="text-muted-foreground">Unknown</span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => window.open(channel.channel_url, '_blank')}
                        >
                          <ExternalLink className="h-3 w-3 mr-1" />
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="text-center py-8">
              <Youtube className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">No channels added yet</h3>
              <p className="text-muted-foreground mb-4">
                Add your first YouTube channel to start monitoring for new uploads
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
