import { useEffect, useState, useCallback } from "react";
import { supabase } from "@/lib/supabase";
import type { ImagePrompt } from "@/lib/types";

export function useImagePrompts() {
  const [prompts, setPrompts] = useState<ImagePrompt[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchPrompts = useCallback(async () => {
    const { data, error } = await supabase
      .from("image_prompts")
      .select("*")
      .order("created_at", { ascending: false })
      .limit(100);

    if (error) {
      console.error("Error fetching image_prompts:", error);
    } else {
      setPrompts((data as ImagePrompt[]) || []);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchPrompts();
    const interval = setInterval(fetchPrompts, 30000);
    return () => clearInterval(interval);
  }, [fetchPrompts]);

  return { prompts, loading, refetch: fetchPrompts };
}
