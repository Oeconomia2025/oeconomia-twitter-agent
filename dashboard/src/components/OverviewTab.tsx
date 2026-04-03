import {
  Activity,
  BarChart3,
  Clock,
  Eye,
  Heart,
  MessageSquare,
  Repeat2,
  TrendingUp,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { format, isToday, isThisWeek, parseISO } from "date-fns";
import type { TwitterPost, AgentState } from "@/lib/types";

interface OverviewTabProps {
  agentState: {
    state: AgentState | null;
    loading: boolean;
  };
  posts: TwitterPost[];
  postsLoading: boolean;
}

export function OverviewTab({
  agentState,
  posts,
  postsLoading,
}: OverviewTabProps) {
  const state = agentState.state;

  const postsToday = posts.filter((p) => isToday(parseISO(p.created_at)));
  const postsThisWeek = posts.filter((p) =>
    isThisWeek(parseISO(p.created_at), { weekStartsOn: 1 })
  );

  const totalImpressions = posts.reduce((sum, p) => sum + (p.impressions || 0), 0);
  const totalEngagement = posts.reduce(
    (sum, p) => sum + (p.likes || 0) + (p.replies || 0) + (p.retweets || 0) + (p.quotes || 0),
    0
  );

  const topPosts = [...posts]
    .sort((a, b) => (b.impressions || 0) - (a.impressions || 0))
    .slice(0, 5);

  // Build chart data: posts per day for the last 7 days
  const chartData = buildDailyChart(posts);

  // Agent status
  const heartbeat = state?.last_heartbeat
    ? new Date(state.last_heartbeat)
    : null;
  const now = new Date();
  const staleMs = heartbeat ? now.getTime() - heartbeat.getTime() : Infinity;

  let agentStatus: "running" | "paused" | "offline" = "offline";
  if (state && !state.is_running) agentStatus = "paused";
  else if (staleMs <= 5 * 60 * 1000) agentStatus = "running";

  return (
    <div className="space-y-6">
      {/* Status + Badges */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Activity className="w-5 h-5" />}
          label="Agent Status"
          value={
            agentStatus === "running"
              ? "Running"
              : agentStatus === "paused"
              ? "Paused"
              : "Offline"
          }
          color={
            agentStatus === "running"
              ? "text-green-400"
              : agentStatus === "paused"
              ? "text-yellow-400"
              : "text-red-400"
          }
          subtext={
            heartbeat
              ? `Last heartbeat: ${format(heartbeat, "h:mm a")}`
              : "No heartbeat"
          }
        />
        <StatCard
          icon={<BarChart3 className="w-5 h-5" />}
          label="Posts Today"
          value={postsToday.length.toString()}
          color="text-accent"
          subtext={`${postsThisWeek.length} this week`}
        />
        <StatCard
          icon={<Eye className="w-5 h-5" />}
          label="Total Impressions"
          value={formatNumber(totalImpressions)}
          color="text-blue-400"
          subtext="All time"
        />
        <StatCard
          icon={<TrendingUp className="w-5 h-5" />}
          label="Total Engagement"
          value={formatNumber(totalEngagement)}
          color="text-purple-400"
          subtext="Likes + Replies + RTs + Quotes"
        />
      </div>

      {/* Config Badges */}
      {state && (
        <div className="flex flex-wrap gap-2">
          <Badge
            label="DRY_RUN"
            value={state.dry_run ? "ON" : "OFF"}
            active={state.dry_run}
            colorOn="bg-orange-500/10 text-orange-400 border-orange-500/30"
            colorOff="bg-gray-800 text-gray-500 border-gray-700"
          />
          <Badge
            label="IMAGE_MODE"
            value={state.image_mode.toUpperCase()}
            active={state.image_mode !== "none"}
            colorOn="bg-cyan-500/10 text-cyan-400 border-cyan-500/30"
            colorOff="bg-gray-800 text-gray-500 border-gray-700"
          />
        </div>
      )}

      {/* Chart */}
      <div className="bg-surface rounded-xl border border-gray-800 p-6">
        <h3 className="text-sm font-medium text-gray-400 mb-4">
          Posts Per Day (Last 7 Days)
        </h3>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis
                dataKey="day"
                tick={{ fill: "#9ca3af", fontSize: 12 }}
                axisLine={{ stroke: "#374151" }}
              />
              <YAxis
                allowDecimals={false}
                tick={{ fill: "#9ca3af", fontSize: 12 }}
                axisLine={{ stroke: "#374151" }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#111827",
                  border: "1px solid #374151",
                  borderRadius: 8,
                  color: "#f3f4f6",
                }}
              />
              <Bar dataKey="count" fill="#00d4ff" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Performing Tweets */}
        <div className="bg-surface rounded-xl border border-gray-800 p-6">
          <h3 className="text-sm font-medium text-gray-400 mb-4">
            Top Performing Tweets
          </h3>
          {topPosts.length === 0 ? (
            <p className="text-gray-600 text-sm">No posts yet</p>
          ) : (
            <div className="space-y-3">
              {topPosts.map((post) => (
                <div
                  key={post.id}
                  className="p-3 bg-gray-900/50 rounded-lg border border-gray-800/50"
                >
                  <p className="text-sm text-gray-300 line-clamp-2">
                    {post.tweet_text}
                  </p>
                  <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                    <span className="flex items-center space-x-1">
                      <Eye className="w-3 h-3" />
                      <span>{formatNumber(post.impressions)}</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <Heart className="w-3 h-3" />
                      <span>{post.likes}</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <MessageSquare className="w-3 h-3" />
                      <span>{post.replies}</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <Repeat2 className="w-3 h-3" />
                      <span>{post.retweets}</span>
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Next Scheduled Posts */}
        <div className="bg-surface rounded-xl border border-gray-800 p-6">
          <h3 className="text-sm font-medium text-gray-400 mb-4">
            <Clock className="w-4 h-4 inline-block mr-1" />
            Next Scheduled Posts
          </h3>
          {!state?.next_post_times || state.next_post_times.length === 0 ? (
            <p className="text-gray-600 text-sm">No upcoming posts scheduled</p>
          ) : (
            <div className="space-y-2">
              {state.next_post_times.map((npt, i) => {
                const postTime = new Date(npt.time);
                const isPast = postTime < now;
                return (
                  <div
                    key={i}
                    className={`flex items-center justify-between p-3 rounded-lg border ${
                      isPast
                        ? "bg-gray-900/30 border-gray-800/30 opacity-50"
                        : "bg-gray-900/50 border-gray-800/50"
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <Clock
                        className={`w-4 h-4 ${
                          isPast ? "text-gray-600" : "text-accent"
                        }`}
                      />
                      <span className="text-sm text-gray-300">
                        {format(postTime, "h:mm a")}
                      </span>
                    </div>
                    <PostTypeBadge type={npt.post_type} />
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ---- Helpers ----

function StatCard({
  icon,
  label,
  value,
  color,
  subtext,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: string;
  subtext: string;
}) {
  return (
    <div className="bg-surface rounded-xl border border-gray-800 p-5">
      <div className="flex items-center space-x-2 text-gray-500 mb-2">
        {icon}
        <span className="text-xs font-medium uppercase tracking-wider">
          {label}
        </span>
      </div>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      <p className="text-xs text-gray-600 mt-1">{subtext}</p>
    </div>
  );
}

function Badge({
  label,
  value,
  active,
  colorOn,
  colorOff,
}: {
  label: string;
  value: string;
  active: boolean;
  colorOn: string;
  colorOff: string;
}) {
  return (
    <span
      className={`px-3 py-1 text-xs rounded-full border ${
        active ? colorOn : colorOff
      }`}
    >
      {label}: {value}
    </span>
  );
}

export function PostTypeBadge({ type }: { type: string }) {
  const colors: Record<string, string> = {
    technical: "bg-blue-500/10 text-blue-400 border-blue-500/30",
    hype: "bg-pink-500/10 text-pink-400 border-pink-500/30",
    educational: "bg-green-500/10 text-green-400 border-green-500/30",
    philosophical: "bg-purple-500/10 text-purple-400 border-purple-500/30",
  };
  const c = colors[type] || "bg-gray-800 text-gray-400 border-gray-700";
  return (
    <span className={`px-2 py-0.5 text-xs rounded-full border ${c}`}>
      {type}
    </span>
  );
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
  return n.toString();
}

function buildDailyChart(posts: TwitterPost[]) {
  const days: Record<string, number> = {};
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const key = format(d, "MMM d");
    days[key] = 0;
  }

  for (const p of posts) {
    const key = format(parseISO(p.created_at), "MMM d");
    if (key in days) {
      days[key]++;
    }
  }

  return Object.entries(days).map(([day, count]) => ({ day, count }));
}
