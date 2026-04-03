export interface TwitterPost {
  id: string;
  post_type: string;
  tweet_text: string;
  hook: string | null;
  hashtags: string[];
  image_prompt: string | null;
  image_style_tags: string[];
  tweet_id: string | null;
  image_path: string | null;
  image_url: string | null;
  status: string;
  impressions: number;
  likes: number;
  replies: number;
  retweets: number;
  quotes: number;
  created_at: string;
  posted_at: string | null;
}

export interface ImagePrompt {
  id: string;
  post_id: string | null;
  post_type: string;
  tweet_text_preview: string;
  image_prompt: string;
  style_tags: string[];
  dalle_path: string | null;
  status: string;
  created_at: string;
}

export interface AgentState {
  id: number;
  is_running: boolean;
  dry_run: boolean;
  image_mode: string;
  last_heartbeat: string | null;
  next_post_times: NextPostTime[];
  created_at: string;
  updated_at: string;
}

export interface NextPostTime {
  time: string;
  post_type: string;
}
