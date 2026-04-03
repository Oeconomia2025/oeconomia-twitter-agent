import { useState } from "react";
import {
  Play,
  Pause,
  Eye,
  EyeOff,
  Image,
  Monitor,
  AlertTriangle,
  CheckCircle,
  Loader2,
} from "lucide-react";
import type { AgentState } from "@/lib/types";

interface ControlsTabProps {
  agentState: {
    state: AgentState | null;
    loading: boolean;
    updateState: (updates: Partial<AgentState>) => Promise<boolean>;
  };
}

export function ControlsTab({ agentState }: ControlsTabProps) {
  const { state, loading, updateState } = agentState;
  const [saving, setSaving] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{
    key: string;
    ok: boolean;
  } | null>(null);

  if (loading || !state) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const handleToggle = async (
    key: string,
    updates: Partial<AgentState>
  ) => {
    setSaving(key);
    setFeedback(null);
    const ok = await updateState(updates);
    setFeedback({ key, ok });
    setSaving(null);
    setTimeout(() => setFeedback(null), 3000);
  };

  return (
    <div className="max-w-2xl space-y-6">
      <div className="bg-surface rounded-xl border border-gray-800 p-6 space-y-1">
        <h2 className="text-lg font-semibold text-white">Agent Controls</h2>
        <p className="text-sm text-gray-500">
          Changes take effect on the next post cycle. The agent reads these
          values from Supabase before each cycle.
        </p>
      </div>

      {/* Pause/Resume */}
      <ControlCard
        title="Agent Status"
        description={
          state.is_running
            ? "Agent is running and will post on schedule."
            : "Agent is paused. No tweets will be posted until resumed."
        }
        icon={state.is_running ? <Play className="w-5 h-5" /> : <Pause className="w-5 h-5" />}
        iconColor={state.is_running ? "text-green-400" : "text-yellow-400"}
      >
        <ToggleButton
          active={state.is_running}
          labelOn="Running"
          labelOff="Paused"
          colorOn="bg-green-500/10 border-green-500/30 text-green-400 hover:bg-green-500/20"
          colorOff="bg-yellow-500/10 border-yellow-500/30 text-yellow-400 hover:bg-yellow-500/20"
          saving={saving === "is_running"}
          feedback={feedback?.key === "is_running" ? feedback : null}
          onClick={() =>
            handleToggle("is_running", {
              is_running: !state.is_running,
            })
          }
        />
      </ControlCard>

      {/* DRY_RUN */}
      <ControlCard
        title="Dry Run Mode"
        description={
          state.dry_run
            ? "Tweets are generated and logged but NOT posted to Twitter."
            : "Tweets will be posted LIVE to Twitter."
        }
        icon={state.dry_run ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
        iconColor={state.dry_run ? "text-orange-400" : "text-cyan-400"}
      >
        <ToggleButton
          active={state.dry_run}
          labelOn="DRY RUN"
          labelOff="LIVE"
          colorOn="bg-orange-500/10 border-orange-500/30 text-orange-400 hover:bg-orange-500/20"
          colorOff="bg-cyan-500/10 border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/20"
          saving={saving === "dry_run"}
          feedback={feedback?.key === "dry_run" ? feedback : null}
          onClick={() =>
            handleToggle("dry_run", { dry_run: !state.dry_run })
          }
        />
      </ControlCard>

      {/* IMAGE_MODE */}
      <ControlCard
        title="Image Mode"
        description={
          state.image_mode === "dalle"
            ? "Images are auto-generated via DALL-E 3 and attached to tweets."
            : state.image_mode === "manual"
            ? "Image prompts are logged for manual creation. No auto-generation."
            : "No images. Text-only tweets."
        }
        icon={<Image className="w-5 h-5" />}
        iconColor="text-purple-400"
      >
        <div className="flex space-x-2">
          {(["manual", "dalle", "none"] as const).map((mode) => (
            <button
              key={mode}
              onClick={() =>
                handleToggle("image_mode", { image_mode: mode })
              }
              disabled={saving === "image_mode"}
              className={`px-4 py-2 text-sm rounded-lg border transition-colors ${
                state.image_mode === mode
                  ? "bg-purple-500/10 border-purple-500/30 text-purple-400"
                  : "bg-gray-900 border-gray-700 text-gray-500 hover:text-gray-300 hover:border-gray-600"
              }`}
            >
              {saving === "image_mode" ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                mode.toUpperCase()
              )}
            </button>
          ))}
          {feedback?.key === "image_mode" && (
            <FeedbackIcon ok={feedback.ok} />
          )}
        </div>
      </ControlCard>

      {/* Post Now - informational */}
      <ControlCard
        title="Manual Post"
        description="To trigger an immediate post, run the agent with a manual command:"
        icon={<Monitor className="w-5 h-5" />}
        iconColor="text-gray-400"
      >
        <div className="bg-gray-900/80 rounded-lg p-3 border border-gray-800">
          <code className="text-sm text-accent">
            python -c "from agent.main import run_post_cycle;
            run_post_cycle('hype')"
          </code>
        </div>
      </ControlCard>

      {/* Warning */}
      <div className="flex items-start space-x-3 p-4 bg-yellow-500/5 border border-yellow-500/20 rounded-xl">
        <AlertTriangle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-yellow-400/80">
          Turning off <strong>DRY_RUN</strong> will post real tweets to
          @CryptoM33156512. Make sure your Twitter credentials are configured
          and you are ready to go live.
        </div>
      </div>
    </div>
  );
}

// ---- Sub-components ----

function ControlCard({
  title,
  description,
  icon,
  iconColor,
  children,
}: {
  title: string;
  description: string;
  icon: React.ReactNode;
  iconColor: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-surface rounded-xl border border-gray-800 p-5 space-y-4">
      <div className="flex items-start space-x-3">
        <div className={iconColor}>{icon}</div>
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-white">{title}</h3>
          <p className="text-xs text-gray-500 mt-0.5">{description}</p>
        </div>
      </div>
      {children}
    </div>
  );
}

function ToggleButton({
  active,
  labelOn,
  labelOff,
  colorOn,
  colorOff,
  saving,
  feedback,
  onClick,
}: {
  active: boolean;
  labelOn: string;
  labelOff: string;
  colorOn: string;
  colorOff: string;
  saving: boolean;
  feedback: { ok: boolean } | null;
  onClick: () => void;
}) {
  return (
    <div className="flex items-center space-x-3">
      <button
        onClick={onClick}
        disabled={saving}
        className={`px-5 py-2 text-sm rounded-lg border transition-colors ${
          active ? colorOn : colorOff
        }`}
      >
        {saving ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : active ? (
          labelOn
        ) : (
          labelOff
        )}
      </button>
      <span className="text-xs text-gray-600">
        Click to {active ? "turn off" : "turn on"}
      </span>
      {feedback && <FeedbackIcon ok={feedback.ok} />}
    </div>
  );
}

function FeedbackIcon({ ok }: { ok: boolean }) {
  return ok ? (
    <CheckCircle className="w-4 h-4 text-green-400" />
  ) : (
    <AlertTriangle className="w-4 h-4 text-red-400" />
  );
}
