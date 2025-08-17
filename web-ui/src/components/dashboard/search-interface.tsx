"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
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
import { 
  Search, 
  TrendingUp, 
  Calendar, 
  ExternalLink,
  RefreshCw,
  Star,
  Hash,
  BarChart3
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { formatDistanceToNow } from "date-fns";

export function SearchInterface() {
  const [searchKeywords, setSearchKeywords] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const { data: trendingTopics, isLoading: trendingLoading } = useQuery({
    queryKey: ['trending-topics'],
    queryFn: () => apiClient.getTrendingTopics(30, 20),
  });

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchKeywords.trim()) return;

    setIsSearching(true);
    try {
      const keywords = searchKeywords.split(',').map(k => k.trim()).filter(k => k);
      const results = await apiClient.searchVideos({ keywords, limit: 50 });
      setSearchResults(results);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return "Unknown";
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-6">
      <Tabs defaultValue="search" className="space-y-6">
        <TabsList>
          <TabsTrigger value="search" className="flex items-center gap-2">
            <Search className="h-4 w-4" />
            Keyword Search
          </TabsTrigger>
          <TabsTrigger value="trending" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Trending Topics
          </TabsTrigger>
        </TabsList>

        <TabsContent value="search">
          {/* Search Form */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5" />
                Search Transcriptions
              </CardTitle>
              <CardDescription>
                Search across all video transcriptions using keywords
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSearch} className="flex gap-4">
                <Input
                  placeholder="artificial intelligence, machine learning, python"
                  value={searchKeywords}
                  onChange={(e) => setSearchKeywords(e.target.value)}
                  className="flex-1"
                />
                <Button 
                  type="submit" 
                  disabled={isSearching || !searchKeywords.trim()}
                >
                  {isSearching ? (
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Search className="h-4 w-4 mr-2" />
                  )}
                  Search
                </Button>
              </form>
              <p className="text-sm text-muted-foreground mt-2">
                Separate multiple keywords with commas. Search will find videos containing any of the keywords.
              </p>
            </CardContent>
          </Card>

          {/* Search Results */}
          {searchResults.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Search Results ({searchResults.length})</CardTitle>
                <CardDescription>
                  Videos matching your search criteria, ranked by relevance
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Video</TableHead>
                        <TableHead>Channel</TableHead>
                        <TableHead>Relevance</TableHead>
                        <TableHead>Matched Keywords</TableHead>
                        <TableHead>Upload Date</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {searchResults.map((result, index) => (
                        <TableRow key={index}>
                          <TableCell>
                            <div className="space-y-1 max-w-xs">
                              <div className="font-medium line-clamp-2">{result.video.title}</div>
                              <div className="text-xs text-muted-foreground">
                                ID: {result.video.video_id}
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="text-sm">{result.video.channel_name}</div>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-1">
                              <Star className="h-3 w-3 text-yellow-500" />
                              <span className="text-sm font-medium">
                                {(result.relevance_score * 100).toFixed(0)}%
                              </span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex flex-wrap gap-1">
                              {result.matched_keywords.slice(0, 3).map((keyword: string, i: number) => (
                                <Badge key={i} variant="secondary" className="text-xs">
                                  {keyword}
                                </Badge>
                              ))}
                              {result.matched_keywords.length > 3 && (
                                <Badge variant="outline" className="text-xs">
                                  +{result.matched_keywords.length - 3}
                                </Badge>
                              )}
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="text-sm">
                              {result.video.upload_date ? (
                                <>
                                  <div>{formatDistanceToNow(new Date(result.video.upload_date))} ago</div>
                                  <div className="text-xs text-muted-foreground">
                                    {new Date(result.video.upload_date).toLocaleDateString()}
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
                              onClick={() => window.open(result.video.url, '_blank')}
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
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="trending">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Trending Topics (Last 30 Days)
              </CardTitle>
              <CardDescription>
                Most frequently mentioned keywords and topics across all transcriptions
              </CardDescription>
            </CardHeader>
            <CardContent>
              {trendingLoading ? (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="h-6 w-6 animate-spin mr-2" />
                  Loading trending topics...
                </div>
              ) : trendingTopics && trendingTopics.length > 0 ? (
                <div className="space-y-4">
                  {/* Top trending topics as cards */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {trendingTopics.slice(0, 6).map((topic, index) => (
                      <Card key={index} className="relative overflow-hidden">
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between">
                            <div className="space-y-2">
                              <div className="font-medium text-lg">{topic.keyword}</div>
                              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                <div className="flex items-center gap-1">
                                  <Hash className="h-3 w-3" />
                                  {topic.frequency} mentions
                                </div>
                                <div className="flex items-center gap-1">
                                  <BarChart3 className="h-3 w-3" />
                                  {topic.video_count} videos
                                </div>
                              </div>
                            </div>
                            <Badge variant="outline" className="text-xs">
                              #{index + 1}
                            </Badge>
                          </div>
                          <div className="mt-3">
                            <div className="text-xs text-muted-foreground mb-1">Trend Score</div>
                            <div className="text-xl font-bold text-blue-600">
                              {topic.trend_score.toFixed(0)}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  {/* Full trending table */}
                  {trendingTopics.length > 6 && (
                    <div className="rounded-md border">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Rank</TableHead>
                            <TableHead>Keyword</TableHead>
                            <TableHead>Frequency</TableHead>
                            <TableHead>Videos</TableHead>
                            <TableHead>Trend Score</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {trendingTopics.slice(6).map((topic, index) => (
                            <TableRow key={index}>
                              <TableCell>
                                <Badge variant="outline">#{index + 7}</Badge>
                              </TableCell>
                              <TableCell>
                                <div className="font-medium">{topic.keyword}</div>
                              </TableCell>
                              <TableCell>
                                <div className="flex items-center gap-1">
                                  <Hash className="h-3 w-3 text-muted-foreground" />
                                  {topic.frequency}
                                </div>
                              </TableCell>
                              <TableCell>
                                <div className="flex items-center gap-1">
                                  <BarChart3 className="h-3 w-3 text-muted-foreground" />
                                  {topic.video_count}
                                </div>
                              </TableCell>
                              <TableCell>
                                <div className="font-medium text-blue-600">
                                  {topic.trend_score.toFixed(0)}
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8">
                  <TrendingUp className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">No trending topics yet</h3>
                  <p className="text-muted-foreground">
                    Trending topics will appear here once you have processed some videos
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
