import { useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  Eye,
  Heart,
  MessageSquare,
  Repeat2,
  Quote,
  Filter,
} from "lucide-react";
import { format, parseISO } from "date-fns";
import { PostTypeBadge } from "./OverviewTab";
import type { TwitterPost } from "@/lib/types";

interface PostsTabProps {
  posts: TwitterPost[];
  loading: boolean;
}

const STATUS_OPTIONS = ["all", "posted", "dry_run", "pending", "failed"];
const TYPE_OPTIONS = [
  "all",
  "technical",
  "hype",
  "educational",
  "philosophical",
];

export function PostsTab({ posts, loading }: PostsTabProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");

  const filtered = posts.filter((p) => {
    if (statusFilter !== "all" && p.status !== statusFilter) return false;
    if (typeFilter !== "all" && p.post_type !== typeFilter) return false;
    return true;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <span className="text-xs text-gray-500 uppercase tracking-wider">
            Filters
          </span>
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-surface border border-gray-700 text-gray-300 text-sm rounded-lg px-3 py-1.5 focus:border-accent focus:outline-none"
        >
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              Status: {s === "all" ? "All" : s}
            </option>
          ))}
        </select>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="bg-surface border border-gray-700 text-gray-300 text-sm rounded-lg px-3 py-1.5 focus:border-accent focus:outline-none"
        >
          {TYPE_OPTIONS.map((t) => (
            <option key={t} value={t}>
              Type: {t === "all" ? "All" : t}
            </option>
          ))}
        </select>
        <span className="text-xs text-gray-600 ml-auto">
          {filtered.length} post{filtered.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Posts List */}
      {filtered.length === 0 ? (
        <div className="text-center py-20 text-gray-600">
          No posts match your filters
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((post) => {
            const isExpanded = expandedId === post.id;
            return (
              <div
                key={post.id}
                className="bg-surface rounded-xl border border-gray-800 overflow-hidden transition-colors hover:border-gray-700"
              >
                {/* Row */}
                <button
                  onClick={() =>
                    setExpandedId(isExpanded ? null : post.id)
                  }
                  className="w-full flex items-center justify-between px-4 py-3 text-left"
                >
                  <div className="flex items-center space-x-3 min-w-0 flex-1">
                    <span className="text-xs text-gray-600 whitespace-nowrap">
                      {format(parseISO(post.created_at), "MMM d, h:mm a")}
                    </span>
                    <PostTypeBadge type={post.post_type} />
                    <StatusBadge status={post.status} />
                    <p className="text-sm text-gray-300 truncate min-w-0">
                      {post.tweet_text}
                    </p>
                  </div>
                  <div className="flex items-center space-x-4 ml-4 flex-shrink-0">
                    <MetricChip
                      icon={<Eye className="w-3 h-3" />}
                      value={post.impressions}
                    />
                    <MetricChip
                      icon={<Heart className="w-3 h-3" />}
                      value={post.likes}
                    />
                    <MetricChip
                      icon={<MessageSquare className="w-3 h-3" />}
                      value={post.replies}
                    />
                    <MetricChip
                      icon={<Repeat2 className="w-3 h-3" />}
                      value={post.retweets}
                    />
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-gray-500" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-gray-500" />
                    )}
                  </div>
                </button>

                {/* Expanded Detail */}
                {isExpanded && (
                  <div className="border-t border-gray-800 px-4 py-4 space-y-3 bg-gray-900/30">
                    <div>
                      <label className="text-xs text-gray-500 uppercase tracking-wider">
                        Full Tweet
                      </label>
                      <p className="text-sm text-gray-200 mt-1 whitespace-pre-wrap">
                        {post.tweet_text}
                      </p>
                    </div>
                    {post.image_url && (
                      <div>
                        <label className="text-xs text-gray-500 uppercase tracking-wider">
                          Generated Image
                        </label>
                        <img
                          src={post.image_url}
                          alt="Generated"
                          className="mt-2 rounded-lg max-h-64 object-contain border border-gray-700"
                        />
                      </div>
                    )}
                    {post.image_prompt && (
                      <div>
                        <label className="text-xs text-gray-500 uppercase tracking-wider">
                          Image Prompt
                        </label>
                        <p className="text-sm text-gray-400 mt-1 italic">
                          {post.image_prompt}
                        </p>
                      </div>
                    )}
                    {post.tweet_id && post.tweet_id !== "DRY_RUN" && (
                      <div>
                        <label className="text-xs text-gray-500 uppercase tracking-wider">
                          Tweet ID
                        </label>
                        <a
                          href={`https://twitter.com/CryptoM33156512/status/${post.tweet_id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-accent hover:underline ml-2"
                        >
                          {post.tweet_id}
                        </a>
                      </div>
                    )}
                    <div className="flex items-center space-x-6 text-xs text-gray-500">
                      <span>
                        Impressions:{" "}
                        <strong className="text-gray-300">
                          {post.impressions.toLocaleString()}
                        </strong>
                      </span>
                      <span>
                        Likes:{" "}
                        <strong className="text-gray-300">{post.likes}</strong>
                      </span>
                      <span>
                        Replies:{" "}
                        <strong className="text-gray-300">
                          {post.replies}
                        </strong>
                      </span>
                      <span>
                        Retweets:{" "}
                        <strong className="text-gray-300">
                          {post.retweets}
                        </strong>
                      </span>
                      <span>
                        Quotes:{" "}
                        <strong className="text-gray-300">
                          {post.quotes}
                        </strong>
                      </span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    posted: "bg-green-500/10 text-green-400 border-green-500/30",
    dry_run: "bg-orange-500/10 text-orange-400 border-orange-500/30",
    pending: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
    failed: "bg-red-500/10 text-red-400 border-red-500/30",
  };
  const c = colors[status] || "bg-gray-800 text-gray-400 border-gray-700";
  return (
    <span className={`px-2 py-0.5 text-xs rounded-full border ${c}`}>
      {status}
    </span>
  );
}

function MetricChip({
  icon,
  value,
}: {
  icon: React.ReactNode;
  value: number;
}) {
  return (
    <span className="hidden sm:flex items-center space-x-1 text-xs text-gray-500">
      {icon}
      <span>{value}</span>
    </span>
  );
}
