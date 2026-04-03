-- ==========================================================================
-- Oeconomia Twitter Agent — Supabase Migration
-- Run this in the Supabase SQL Editor to create all required tables.
-- ==========================================================================

-- 1. twitter_posts — stores every generated/posted tweet
CREATE TABLE IF NOT EXISTS twitter_posts (
    id              uuid            DEFAULT gen_random_uuid() PRIMARY KEY,
    post_type       text            NOT NULL,
    tweet_text      text            NOT NULL,
    hook            text,
    hashtags        jsonb           DEFAULT '[]'::jsonb,
    image_prompt    text,
    image_style_tags jsonb          DEFAULT '[]'::jsonb,
    tweet_id        text,
    image_path      text,
    status          text            DEFAULT 'pending',
    impressions     int             DEFAULT 0,
    likes           int             DEFAULT 0,
    replies         int             DEFAULT 0,
    retweets        int             DEFAULT 0,
    quotes          int             DEFAULT 0,
    created_at      timestamptz     DEFAULT now(),
    posted_at       timestamptz
);

-- 2. image_prompts — tracks every image prompt generated
CREATE TABLE IF NOT EXISTS image_prompts (
    id                  uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
    post_id             uuid        REFERENCES twitter_posts(id) ON DELETE SET NULL,
    post_type           text        NOT NULL,
    tweet_text_preview  text,
    image_prompt        text,
    style_tags          jsonb       DEFAULT '[]'::jsonb,
    dalle_path          text,
    status              text        DEFAULT 'pending',
    created_at          timestamptz DEFAULT now()
);

-- 3. agent_state — singleton row for dashboard ↔ agent communication
CREATE TABLE IF NOT EXISTS agent_state (
    id              int             DEFAULT 1 PRIMARY KEY CHECK (id = 1),
    is_running      boolean         DEFAULT true,
    dry_run         boolean         DEFAULT true,
    image_mode      text            DEFAULT 'manual',
    last_heartbeat  timestamptz,
    next_post_times jsonb           DEFAULT '[]'::jsonb,
    created_at      timestamptz     DEFAULT now(),
    updated_at      timestamptz     DEFAULT now()
);

-- Insert the default agent_state row
INSERT INTO agent_state (id, is_running, dry_run, image_mode, last_heartbeat, created_at, updated_at)
VALUES (1, true, true, 'manual', now(), now(), now())
ON CONFLICT (id) DO NOTHING;

-- ==========================================================================
-- Row Level Security (RLS)
-- ==========================================================================

ALTER TABLE twitter_posts  ENABLE ROW LEVEL SECURITY;
ALTER TABLE image_prompts  ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_state    ENABLE ROW LEVEL SECURITY;

-- twitter_posts policies
CREATE POLICY "twitter_posts_select_anon"
    ON twitter_posts FOR SELECT
    TO anon, authenticated
    USING (true);

CREATE POLICY "twitter_posts_insert_service"
    ON twitter_posts FOR INSERT
    TO service_role
    WITH CHECK (true);

CREATE POLICY "twitter_posts_update_service"
    ON twitter_posts FOR UPDATE
    TO service_role
    USING (true)
    WITH CHECK (true);

-- image_prompts policies
CREATE POLICY "image_prompts_select_anon"
    ON image_prompts FOR SELECT
    TO anon, authenticated
    USING (true);

CREATE POLICY "image_prompts_insert_service"
    ON image_prompts FOR INSERT
    TO service_role
    WITH CHECK (true);

CREATE POLICY "image_prompts_update_service"
    ON image_prompts FOR UPDATE
    TO service_role
    USING (true)
    WITH CHECK (true);

-- agent_state policies
CREATE POLICY "agent_state_select_anon"
    ON agent_state FOR SELECT
    TO anon, authenticated
    USING (true);

CREATE POLICY "agent_state_insert_service"
    ON agent_state FOR INSERT
    TO service_role
    WITH CHECK (true);

CREATE POLICY "agent_state_update_service"
    ON agent_state FOR UPDATE
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Allow anon to update agent_state (for dashboard controls)
CREATE POLICY "agent_state_update_anon"
    ON agent_state FOR UPDATE
    TO anon, authenticated
    USING (true)
    WITH CHECK (true);

-- ==========================================================================
-- Indexes for common queries
-- ==========================================================================

CREATE INDEX IF NOT EXISTS idx_twitter_posts_created_at ON twitter_posts (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_twitter_posts_status     ON twitter_posts (status);
CREATE INDEX IF NOT EXISTS idx_twitter_posts_post_type  ON twitter_posts (post_type);
CREATE INDEX IF NOT EXISTS idx_twitter_posts_tweet_id   ON twitter_posts (tweet_id);
CREATE INDEX IF NOT EXISTS idx_image_prompts_post_id    ON image_prompts (post_id);
CREATE INDEX IF NOT EXISTS idx_image_prompts_status     ON image_prompts (status);
