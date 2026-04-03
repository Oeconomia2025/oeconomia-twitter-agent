import { useEffect, useState, useCallback } from "react";
import { supabase } from "@/lib/supabase";
import type { AgentState } from "@/lib/types";

export function useAgentState() {
  const [state, setState] = useState<AgentState | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchState = useCallback(async () => {
    const { data, error } = await supabase
      .from("agent_state")
      .select("*")
      .eq("id", 1)
      .single();

    if (error) {
      console.error("Error fetching agent_state:", error);
    } else {
      setState(data as AgentState);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchState();
    const interval = setInterval(fetchState, 15000); // Poll every 15s
    return () => clearInterval(interval);
  }, [fetchState]);

  const updateState = async (updates: Partial<AgentState>) => {
    const { error } = await supabase
      .from("agent_state")
      .update({ ...updates, updated_at: new Date().toISOString() })
      .eq("id", 1);

    if (error) {
      console.error("Error updating agent_state:", error);
      return false;
    }
    await fetchState();
    return true;
  };

  return { state, loading, refetch: fetchState, updateState };
}
