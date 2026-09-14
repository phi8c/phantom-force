import React from 'react';
import { 
  GitFork, 
  Layers, 
  Cpu, 
  AlertTriangle, 
  Activity, 
  Settings 
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  onSelectTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onSelectTab }) => {
  const menuItems = [
    { id: 'pipeline-orchestrator', label: 'Pipeline Orchestrator', icon: GitFork },
    { id: 'batch-monitor', label: 'Batch Monitor', icon: Layers },
    { id: 'worker-fleet', label: 'Worker Fleet', icon: Cpu },
    { id: 'dlq-error-logs', label: 'DLQ & Error Logs', icon: AlertTriangle },
    { id: 'metrics-latency', label: 'Metrics & Latency', icon: Activity },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-56 shrink-0 bg-[#070b13] border-r border-slate-800/80 flex flex-col justify-between p-3 select-none">
      {/* Navigation Engines */}
      <div>
        <div className="px-2 pt-1 pb-2">
          <span className="text-[11px] font-semibold text-slate-500 tracking-wider uppercase">
            Execution Engines
          </span>
        </div>

        <nav className="space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                id={`sidebar-nav-${item.id}`}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-[#2563eb] text-white shadow-sm shadow-blue-500/20'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
              >
                <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <span className="truncate">{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Engine Runtime Status Box */}
      <div className="bg-[#0b101c] border border-slate-800/90 rounded-md p-3 space-y-2.5">
        <div className="flex items-center justify-between text-xs">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 font-mono">
            ENGINE RUNTIME
          </span>
          <span className="text-emerald-400 font-mono text-[11px] font-medium">
            v4.12-stream
          </span>
        </div>

        <div className="space-y-1">
          <div className="flex items-center justify-between text-[11px] text-slate-400">
            <span>Buffer Headroom</span>
            <span className="font-mono text-slate-300 font-medium">74.2%</span>
          </div>
          {/* Progress bar */}
          <div className="w-full bg-slate-800/80 h-1.5 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full transition-all duration-700" 
              style={{ width: '74.2%' }}
            />
          </div>
        </div>
      </div>
    </aside>
  );
};
