import React from 'react';
import { 
  Binary, 
  RotateCw, 
  Terminal, 
  Code2, 
  Trash2,
  CheckCircle2
} from 'lucide-react';
import { DagNodeInfo, LogEntry } from '../types';

interface NodeDiagnosticPanelProps {
  selectedNode: DagNodeInfo;
  logs: LogEntry[];
  onDrainBuffer: () => void;
  onOpenAstModal: () => void;
}

export const NodeDiagnosticPanel: React.FC<NodeDiagnosticPanelProps> = ({
  selectedNode,
  logs,
  onDrainBuffer,
  onOpenAstModal,
}) => {
  return (
    <div className="bg-[#0b101c] border border-slate-800/80 rounded-lg p-5 flex flex-col justify-between shadow-sm">
      {/* Top Header */}
      <div>
        <div className="flex items-center justify-between pb-3 border-b border-slate-800/70">
          <div className="flex items-center gap-2.5">
            <Binary className="w-4 h-4 text-purple-400" />
            <h3 className="text-base font-bold text-white tracking-tight font-sans">
              Node Diagnostic
            </h3>
          </div>

          <span className="text-[11px] font-mono font-bold uppercase tracking-wider bg-purple-600 text-white px-2.5 py-1 rounded shadow-sm shadow-purple-600/30">
            {selectedNode.id === 4 
              ? 'STAGE 4 • CHUNKING & FORK' 
              : `STAGE ${selectedNode.id} • ${selectedNode.name.replace(/^\d+\.\s*/, '').toUpperCase()}`}
          </span>
        </div>

        {/* Node Subtitle & Description */}
        <div className="mt-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-white font-mono">
              {selectedNode.id === 4 ? 'Chunking / Fork Router Node' : `${selectedNode.name} Engine`}
            </span>
            <span className="text-[11px] font-mono text-emerald-400 font-semibold">
              {selectedNode.nodeHealth}
            </span>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed font-sans font-normal">
            {selectedNode.description}
          </p>
        </div>

        {/* Two Metric Stat Cards */}
        <div className="grid grid-cols-2 gap-3 mt-4">
          <div className="bg-[#0d1424] border border-slate-800/90 rounded-md p-3">
            <div className="text-[10px] uppercase font-mono font-semibold tracking-wider text-slate-400">
              {selectedNode.stat1Title}
            </div>
            <div className="text-lg font-bold text-white font-mono tracking-tight mt-0.5">
              {selectedNode.stat1Value}
            </div>
            <div className="text-[10px] font-mono text-emerald-400 mt-0.5">
              {selectedNode.stat1Sub}
            </div>
          </div>

          <div className="bg-[#0d1424] border border-slate-800/90 rounded-md p-3">
            <div className="text-[10px] uppercase font-mono font-semibold tracking-wider text-slate-400">
              {selectedNode.stat2Title}
            </div>
            <div className="text-lg font-bold text-white font-mono tracking-tight mt-0.5">
              {selectedNode.stat2Value}
            </div>
            <div className="text-[10px] font-mono text-slate-400 mt-0.5">
              {selectedNode.stat2Sub}
            </div>
          </div>
        </div>

        {/* Live Tail Event Logs */}
        <div className="mt-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-mono uppercase tracking-wider font-semibold text-slate-400">
              LIVE TAIL EVENT LOGS
            </span>

            <div className="flex items-center gap-1.5">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 tracking-wider">
                STREAMING
              </span>
            </div>
          </div>

          {/* Log Window */}
          <div className="bg-[#060a12] border border-slate-900 rounded-md p-3 font-mono text-[11px] leading-snug space-y-1.5 max-h-48 overflow-y-auto">
            {logs.map((log, index) => (
              <div key={index} className="flex items-start gap-2">
                <span className="text-slate-500 shrink-0 select-none">
                  {log.timestamp}
                </span>

                {log.tag && (
                  <span className={`shrink-0 font-medium ${log.tagColor || 'text-slate-300'}`}>
                    {log.tag}
                  </span>
                )}

                {log.isReadySync ? (
                  <div className="flex items-center gap-1.5 text-slate-300">
                    <span className="text-emerald-400 text-xs">•</span>
                    <span>{log.message}</span>
                  </div>
                ) : (
                  <span className="text-slate-300">
                    {log.message}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-2 gap-3 mt-5 pt-3 border-t border-slate-800/70">
        <button
          id="drain-buffer-btn"
          onClick={onDrainBuffer}
          className="flex items-center justify-center gap-1.5 px-3 py-2 bg-[#121927] hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 rounded-md text-xs font-mono font-medium transition-colors"
        >
          <Trash2 className="w-3.5 h-3.5 text-slate-400" />
          <span>Drain Buffer</span>
        </button>

        <button
          id="view-json-ast-btn"
          onClick={onOpenAstModal}
          className="flex items-center justify-center gap-1.5 px-3 py-2 bg-[#1e40af] hover:bg-blue-600 text-white rounded-md text-xs font-mono font-semibold transition-colors shadow-sm shadow-blue-900/30"
        >
          <Code2 className="w-3.5 h-3.5 text-blue-200" />
          <span>View JSON AST</span>
        </button>
      </div>
    </div>
  );
};
