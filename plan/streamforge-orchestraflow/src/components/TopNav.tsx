import React from 'react';
import { 
  Cloud, 
  ChevronsUpDown, 
  Search, 
  RefreshCw, 
  User,
  SlidersHorizontal,
  ChevronDown
} from 'lucide-react';

interface TopNavProps {
  isLive: boolean;
  onToggleLive: () => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  selectedCluster: string;
  onChangeCluster: (c: string) => void;
}

export const TopNav: React.FC<TopNavProps> = ({
  isLive,
  onToggleLive,
  searchQuery,
  onSearchChange,
  selectedCluster,
}) => {
  return (
    <header className="h-14 border-b border-slate-800/80 bg-[#090d16] flex items-center justify-between px-4 sticky top-0 z-30 select-none">
      {/* Left: Brand & Cluster info */}
      <div className="flex items-center gap-3.5">
        {/* Brand Logo & Name */}
        <div className="flex items-center gap-2">
          {/* Multi-lobed cluster logo */}
          <div className="relative w-6 h-6 flex items-center justify-center">
            <div className="w-2.5 h-2.5 rounded-full bg-rose-500 absolute -top-0.5" />
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 absolute -bottom-0.5" />
            <div className="w-2.5 h-2.5 rounded-full bg-sky-400 absolute -left-0.5" />
            <div className="w-2.5 h-2.5 rounded-full bg-amber-400 absolute -right-0.5" />
            <div className="w-1.5 h-1.5 rounded-full bg-indigo-950 z-10 border border-slate-700" />
          </div>

          <div className="flex items-center text-[15px] font-semibold tracking-tight">
            <span className="text-white font-bold">StreamForge</span>
            <span className="text-slate-600 mx-2 font-normal">/</span>
            <span className="text-slate-300 font-medium">OrchestraFlow</span>
          </div>
        </div>

        {/* Environment Badge / Selector */}
        <div className="relative group">
          <button 
            id="cluster-selector-btn"
            className="flex items-center gap-2 px-2.5 py-1 bg-[#121927] hover:bg-[#182235] border border-slate-800/90 hover:border-slate-700 rounded-md text-xs font-mono text-slate-300 transition-colors shadow-inner"
          >
            <Cloud className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span className="tracking-tight">{selectedCluster}</span>
            <ChevronsUpDown className="w-3 h-3 text-slate-500" />
          </button>
        </div>

        {/* Cluster Healthy Status Pill */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-950/40 border border-emerald-500/30 rounded-md">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-[11px] font-bold text-emerald-400 tracking-wider">CLUSTER HEALTHY</span>
        </div>

        {/* Ingestion & Telemetry Quick Stats */}
        <div className="hidden xl:flex items-center gap-4 text-xs font-mono pl-2 border-l border-slate-800/80">
          <div className="flex items-center gap-1 text-slate-400">
            <span>INGESTION:</span>
            <span className="text-slate-200 font-semibold">1,420</span>
            <span className="text-slate-400 text-[11px]">docs/s</span>
          </div>

          <div className="flex items-center gap-1 text-slate-400">
            <span>WORKERS:</span>
            <span className="text-slate-200 font-semibold">64/64</span>
          </div>

          <div className="flex items-center gap-1 text-slate-400">
            <span>LATENCY:</span>
            <span className="text-emerald-400 font-semibold">840ms</span>
          </div>
        </div>
      </div>

      {/* Right: Search, Live Indicator, User Profile */}
      <div className="flex items-center gap-3">
        {/* Search input with shortcut badge */}
        <div className="relative flex items-center">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 pointer-events-none" />
          <input
            id="global-search-input"
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Filter telemetry, DAG nodes, traces (cmd + k)..."
            className="h-8 pl-8 pr-3 text-xs bg-[#0e1524]/90 border border-slate-800/90 rounded-md text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 w-64 md:w-80 font-mono transition-all"
          />
        </div>

        {/* Live Stream Status Toggle Button */}
        <button
          id="toggle-live-stream-btn"
          onClick={onToggleLive}
          title="Toggle 1-second continuous telemetry polling"
          className={`h-8 px-2.5 flex items-center gap-1.5 rounded-md border text-[11px] font-mono font-semibold transition-all ${
            isLive
              ? 'bg-emerald-950/50 text-emerald-400 border-emerald-500/40 hover:bg-emerald-950/70 shadow-sm shadow-emerald-900/20'
              : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
          }`}
        >
          <RefreshCw className={`w-3 h-3 ${isLive ? 'animate-spin text-emerald-400' : 'text-slate-500'}`} style={{ animationDuration: '4s' }} />
          <span>1S LIVE</span>
        </button>

        {/* User Avatar */}
        <button
          id="user-profile-btn"
          className="w-8 h-8 rounded-full bg-[#121927] border border-slate-700/70 flex items-center justify-center text-slate-300 hover:text-white hover:border-slate-500 transition-colors"
        >
          <User className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
