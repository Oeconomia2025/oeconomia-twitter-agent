import { Image, Clock, CheckCircle, XCircle, AlertTriangle } from "lucide-react";
import { format, parseISO } from "date-fns";
import { PostTypeBadge } from "./OverviewTab";
import type { ImagePrompt } from "@/lib/types";

interface ImageQueueTabProps {
  prompts: ImagePrompt[];
  loading: boolean;
}

export function ImageQueueTab({ prompts, loading }: ImageQueueTabProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (prompts.length === 0) {
    return (
      <div className="text-center py-20">
        <Image className="w-12 h-12 text-gray-700 mx-auto mb-3" />
        <p className="text-gray-600">No image prompts in queue</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider">
          Image Prompts ({prompts.length})
        </h2>
        <div className="flex items-center space-x-3 text-xs text-gray-500">
          <StatusLegendItem
            color="text-yellow-400"
            icon={<Clock className="w-3 h-3" />}
            label="Pending"
          />
          <StatusLegendItem
            color="text-green-400"
            icon={<CheckCircle className="w-3 h-3" />}
            label="Generated"
          />
          <StatusLegendItem
            color="text-red-400"
            icon={<XCircle className="w-3 h-3" />}
            label="Blocked"
          />
        </div>
      </div>

      {prompts.map((prompt) => (
        <div
          key={prompt.id}
          className="bg-surface rounded-xl border border-gray-800 p-4 space-y-3"
        >
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <PromptStatusIcon status={prompt.status} />
              <PostTypeBadge type={prompt.post_type} />
              <span className="text-xs text-gray-600">
                {format(parseISO(prompt.created_at), "MMM d, h:mm a")}
              </span>
            </div>
            <PromptStatusBadge status={prompt.status} />
          </div>

          {/* Tweet Preview */}
          <div className="bg-gray-900/50 rounded-lg p-3 border border-gray-800/50">
            <label className="text-xs text-gray-600 uppercase tracking-wider">
              Tweet Preview
            </label>
            <p className="text-sm text-gray-400 mt-1">
              {prompt.tweet_text_preview}
              {prompt.tweet_text_preview.length >= 80 && "..."}
            </p>
          </div>

          {/* Image Prompt */}
          {prompt.image_prompt && (
            <div>
              <label className="text-xs text-gray-500 uppercase tracking-wider">
                Image Prompt
              </label>
              <p className="text-sm text-gray-300 mt-1 leading-relaxed">
                {prompt.image_prompt}
              </p>
            </div>
          )}

          {/* Style Tags */}
          {prompt.style_tags && prompt.style_tags.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {prompt.style_tags.map((tag, i) => (
                <span
                  key={i}
                  className="px-2 py-0.5 text-xs rounded-full bg-gray-800 text-gray-500 border border-gray-700"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* DALL-E Path */}
          {prompt.dalle_path && (
            <p className="text-xs text-gray-600">
              Path: <code className="text-gray-500">{prompt.dalle_path}</code>
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

function PromptStatusIcon({ status }: { status: string }) {
  switch (status) {
    case "generated":
    case "dalle_generated":
    case "posted":
      return <CheckCircle className="w-4 h-4 text-green-400" />;
    case "policy_blocked":
    case "blocked":
      return <XCircle className="w-4 h-4 text-red-400" />;
    case "manual_pending":
    case "pending":
      return <Clock className="w-4 h-4 text-yellow-400" />;
    case "skipped":
      return <AlertTriangle className="w-4 h-4 text-gray-500" />;
    default:
      return <Clock className="w-4 h-4 text-gray-500" />;
  }
}

function PromptStatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    generated: "bg-green-500/10 text-green-400 border-green-500/30",
    dalle_generated: "bg-green-500/10 text-green-400 border-green-500/30",
    posted: "bg-green-500/10 text-green-400 border-green-500/30",
    manual_pending: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
    pending: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
    policy_blocked: "bg-red-500/10 text-red-400 border-red-500/30",
    blocked: "bg-red-500/10 text-red-400 border-red-500/30",
    skipped: "bg-gray-800 text-gray-500 border-gray-700",
  };
  const c = colors[status] || "bg-gray-800 text-gray-400 border-gray-700";
  return (
    <span className={`px-2 py-0.5 text-xs rounded-full border ${c}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}

function StatusLegendItem({
  color,
  icon,
  label,
}: {
  color: string;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <span className={`flex items-center space-x-1 ${color}`}>
      {icon}
      <span>{label}</span>
    </span>
  );
}
