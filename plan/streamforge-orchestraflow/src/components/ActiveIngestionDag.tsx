import React, { useEffect, useState } from 'react';
import { 
  GitFork, 
  Layers, 
  Radio, 
  Download, 
  FileCode2, 
  Split,
  CheckCircle2
} from 'lucide-react';
import { DagNodeInfo } from '../types';

interface ActiveIngestionDagProps {
  nodes: DagNodeInfo[];
  selectedNodeId: number;
  onSelectNode: (nodeId: number) => void;
}

export const ActiveIngestionDag: React.FC<ActiveIngestionDagProps> = ({
  nodes,
  selectedNodeId,
  onSelectNode,
}) => {
  // Live UTC Clock with milliseconds
  const [clockStr, setClockStr] = useState('02:56:16.532 UTC');

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      const hours = String(now.getUTCHours()).padStart(2, '0');
      const minutes = String(now.getUTCMinutes()).padStart(2, '0');
      const seconds = String(now.getUTCSeconds()).padStart(2, '0');
      const ms = String(now.getUTCMilliseconds()).padStart(3, '0');
      setClockStr(`${hours}:${minutes}:${seconds}.${ms} UTC`);
    };

    const interval = setInterval(updateClock, 47); // fast tick for smooth milliseconds
    return () => clearInterval(interval);
  }, []);

  const getNodeIcon = (id: number) => {
    switch (id) {
      case 1:
        return Radio;
      case 2:
        return Download;
      case 3:
        return FileCode2;
      case 4:
      default:
        return Split;
    }
  };

  return (
    <div className="bg-[#0b101c] border-b border-slate-800/80 px-6 py-5 select-none relative overflow-hidden">
      {/* DAG Header & Legend */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          {/* Pulsing Green Dot */}
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400"></span>
          </span>

          <h2 className="text-base font-bold text-white tracking-tight">
            Active Ingestion Graph (DAG)
          </h2>

          <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-slate-300 bg-slate-800/70 border border-slate-700/60 px-2.5 py-0.5 rounded">
            STREAMING CONTIGUOUS PIPELINE
          </span>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-5 text-xs text-slate-300 font-mono">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-sky-400"></span>
            <span>Streaming In-Flight</span>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span>99.9% Health</span>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-teal-400"></span>
            <span>Parallel Fork</span>
          </div>
        </div>
      </div>

      {/* DAG Flow Canvas */}
      <div className="relative py-2">
        {/* SVG Conduit Lines with glowing animated dash pulses */}
        <div className="absolute inset-0 pointer-events-none hidden lg:block">
          <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="dagLineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#0284c7" stopOpacity="0.4" />
                <stop offset="50%" stopColor="#38bdf8" stopOpacity="0.8" />
                <stop offset="100%" stopColor="#818cf8" stopOpacity="0.9" />
              </linearGradient>
              <linearGradient id="forkGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#818cf8" stopOpacity="0.9" />
                <stop offset="100%" stopColor="#2dd4bf" stopOpacity="0.7" />
              </linearGradient>
            </defs>

            {/* Connecting line 1 -> 2 */}
            <line 
              x1="22%" y1="50%" x2="26%" y2="50%" 
              stroke="#38bdf8" strokeWidth="2" strokeDasharray="4 4" 
              className="animate-flow-dash" 
            />
            {/* Connecting line 2 -> 3 */}
            <line 
              x1="46%" y1="50%" x2="50%" y2="50%" 
              stroke="#38bdf8" strokeWidth="2" strokeDasharray="4 4" 
              className="animate-flow-dash" 
            />
            {/* Connecting line 3 -> 4 */}
            <line 
              x1="70%" y1="50%" x2="74%" y2="50%" 
              stroke="#818cf8" strokeWidth="2" strokeDasharray="4 4" 
              className="animate-flow-dash" 
            />

            {/* Right-side Fork Cables extending from Node 4 */}
            {/* Branch A (upper fork) */}
            <path 
              d="M 94% 50% C 97% 50%, 98% 30%, 101% 25%" 
              fill="none" 
              stroke="url(#forkGrad)" 
              strokeWidth="2.5" 
              strokeDasharray="5 4" 
              className="animate-flow-dash" 
            />
            {/* Branch B (lower fork) */}
            <path 
              d="M 94% 50% C 97% 50%, 98% 70%, 101% 75%" 
              fill="none" 
              stroke="url(#forkGrad)" 
              strokeWidth="2.5" 
              strokeDasharray="5 4" 
              className="animate-flow-dash" 
            />

            {/* Branch nodes at far right */}
            <circle cx="98.5%" cy="32%" r="4" fill="#2dd4bf" className="animate-ping" style={{ animationDuration: '3s' }} />
            <circle cx="98.5%" cy="32%" r="3" fill="#2dd4bf" />
            <circle cx="98.5%" cy="68%" r="4" fill="#818cf8" className="animate-ping" style={{ animationDuration: '3s', animationDelay: '1s' }} />
            <circle cx="98.5%" cy="68%" r="3" fill="#818cf8" />
          </svg>
        </div>

        {/* 4 Stage Node Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 relative z-10 pr-0 lg:pr-8">
          {nodes.map((node) => {
            const isSelected = selectedNodeId === node.id;
            const Icon = getNodeIcon(node.id);

            // Badge styling
            let badgeBg = 'bg-emerald-950/60 text-emerald-400 border-emerald-500/40';
            if (node.badgeColor === 'blue') badgeBg = 'bg-sky-950/60 text-sky-400 border-sky-500/40';
            if (node.badgeColor === 'purple') badgeBg = 'bg-purple-950/70 text-purple-300 border-purple-500/50';

            return (
              <div
                key={node.id}
                id={`dag-node-${node.id}`}
                onClick={() => onSelectNode(node.id)}
                className={`group cursor-pointer rounded-lg p-3.5 transition-all duration-200 relative ${
                  isSelected
                    ? 'bg-[#10172e] border-2 border-purple-500/70 shadow-lg shadow-purple-950/40 ring-1 ring-purple-500/30'
                    : 'bg-[#0e1526]/80 hover:bg-[#121b30] border border-slate-800/90 hover:border-slate-700'
                }`}
              >
                {/* Connector plug indicator on left and right */}
                <div className="hidden lg:block absolute -left-1.5 top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-slate-900 border-2 border-slate-700" />
                <div className="hidden lg:block absolute -right-1.5 top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-slate-900 border-2 border-slate-700" />

                {/* Node Title & Badge */}
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <div className={`p-1 rounded ${isSelected ? 'bg-purple-500/20 text-purple-300' : 'bg-slate-800 text-slate-300'}`}>
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <span className="text-xs font-bold text-white font-mono tracking-tight">
                      {node.name}
                    </span>
                  </div>

                  <span className={`text-[10px] font-mono font-bold tracking-wider px-2 py-0.5 rounded border ${badgeBg}`}>
                    {node.badge}
                  </span>
                </div>

                {/* Subtitle / Providers */}
                <div className="text-[11px] text-slate-400 font-mono mb-3 truncate">
                  {node.subtitle}
                </div>

                {/* Metrics Table inside card */}
                <div className="space-y-1.5 text-xs font-mono border-t border-slate-800/80 pt-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400 text-[11px]">{node.rateLabel}</span>
                    <span className="text-slate-200 font-medium text-[11px]">{node.rateValue}</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-400 text-[11px]">{node.metric2Label}</span>
                    <span className={`font-semibold text-[11px] ${node.metric2Color || 'text-slate-200'}`}>
                      {node.metric2Value}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-400 text-[11px]">{node.batchLabel}</span>
                    <span className="text-slate-300 font-medium text-[11px]">{node.batchValue}</span>
                  </div>
                </div>

                {/* Selected Indicator Glow Line */}
                {isSelected && (
                  <div className="absolute inset-x-0 bottom-0 h-0.5 bg-gradient-to-r from-purple-500 via-indigo-400 to-purple-500 rounded-b-lg" />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Bottom Info Bar of DAG */}
      <div className="mt-4 pt-3 border-t border-slate-800/60 flex flex-wrap items-center justify-between gap-4 text-xs font-mono text-slate-400">
        <div className="flex items-center gap-2">
          <GitFork className="w-4 h-4 text-teal-400 shrink-0" />
          <span className="text-slate-300 font-medium">Concurrent Split Mode:</span>
          <span className="text-slate-400">Fully Independent Non-Blocking Queue</span>
          <span className="text-slate-600 hidden md:inline">•</span>
          <span className="text-emerald-400 font-medium hidden md:inline">Zero-Memory Backpressure Active</span>
        </div>

        <div className="flex items-center gap-2">
          <span>DAG Version:</span>
          <span className="text-slate-200 font-semibold">dag-v2.19.0-prod</span>
          <span className="text-slate-600">•</span>
          <span>Sync Clock:</span>
          <span className="text-emerald-400 font-semibold">{clockStr}</span>
        </div>
      </div>
    </div>
  );
};
