import { useState } from "react";
import {
  LayoutDashboard,
  FileText,
  Image,
  Settings,
  Twitter,
} from "lucide-react";
import { OverviewTab } from "@/components/OverviewTab";
import { PostsTab } from "@/components/PostsTab";
import { ImageQueueTab } from "@/components/ImageQueueTab";
import { ControlsTab } from "@/components/ControlsTab";
import { useAgentState } from "@/hooks/useAgentState";
import { usePosts } from "@/hooks/usePosts";
import { useImagePrompts } from "@/hooks/useImagePrompts";

const TABS = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "posts", label: "Posts", icon: FileText },
  { id: "images", label: "Image Queue", icon: Image },
  { id: "controls", label: "Controls", icon: Settings },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function App() {
  const [activeTab, setActiveTab] = useState<TabId>("overview");
  const agentState = useAgentState();
  const postsData = usePosts();
  const imageData = useImagePrompts();

  return (
    <div className="min-h-screen bg-[#0b1016] text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 bg-[#0d1219]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
                <Twitter className="w-4 h-4 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-white">
                  Oeconomia Twitter Agent
                </h1>
                <p className="text-xs text-gray-500">Dashboard</p>
              </div>
            </div>
            <AgentStatusBadge state={agentState.state} />
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="border-b border-gray-800 bg-[#0d1219]/80 sticky top-0 z-10 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-1 overflow-x-auto py-2">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
                    isActive
                      ? "bg-accent/10 text-accent border border-accent/30"
                      : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/50"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === "overview" && (
          <OverviewTab
            agentState={agentState}
            posts={postsData.posts}
            postsLoading={postsData.loading}
          />
        )}
        {activeTab === "posts" && (
          <PostsTab posts={postsData.posts} loading={postsData.loading} />
        )}
        {activeTab === "images" && (
          <ImageQueueTab
            prompts={imageData.prompts}
            loading={imageData.loading}
          />
        )}
        {activeTab === "controls" && (
          <ControlsTab agentState={agentState} />
        )}
      </main>
    </div>
  );
}

function AgentStatusBadge({
  state,
}: {
  state: ReturnType<typeof useAgentState>["state"];
}) {
  if (!state) {
    return (
      <span className="px-3 py-1 text-xs rounded-full bg-gray-800 text-gray-500 border border-gray-700">
        Loading...
      </span>
    );
  }

  const heartbeat = state.last_heartbeat
    ? new Date(state.last_heartbeat)
    : null;
  const now = new Date();
  const staleMs = heartbeat ? now.getTime() - heartbeat.getTime() : Infinity;

  let statusColor: string;
  let statusText: string;

  if (!state.is_running) {
    statusColor = "bg-yellow-500/10 text-yellow-400 border-yellow-500/30";
    statusText = "Paused";
  } else if (staleMs > 5 * 60 * 1000) {
    statusColor = "bg-red-500/10 text-red-400 border-red-500/30";
    statusText = "Offline";
  } else {
    statusColor = "bg-green-500/10 text-green-400 border-green-500/30";
    statusText = "Running";
  }

  return (
    <div className="flex items-center space-x-2">
      {state.dry_run && (
        <span className="px-2 py-1 text-xs rounded-full bg-orange-500/10 text-orange-400 border border-orange-500/30">
          DRY RUN
        </span>
      )}
      <span
        className={`px-3 py-1 text-xs rounded-full border ${statusColor}`}
      >
        {statusText}
      </span>
    </div>
  );
}
