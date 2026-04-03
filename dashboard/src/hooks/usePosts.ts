import { useEffect, useState, useCallback } from "react";
import { supabase } from "@/lib/supabase";
import type { TwitterPost } from "@/lib/types";

export function usePosts() {
  const [posts, setPosts] = useState<TwitterPost[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchPosts = useCallback(async () => {
    const { data, error } = await supabase
      .from("twitter_posts")
      .select("*")
      .order("created_at", { ascending: false })
      .limit(200);

    if (error) {
      console.error("Error fetching twitter_posts:", error);
    } else {
      setPosts((data as TwitterPost[]) || []);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchPosts();
    const interval = setInterval(fetchPosts, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, [fetchPosts]);

  return { posts, loading, refetch: fetchPosts };
}
