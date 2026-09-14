import React, { useState } from 'react';
import { 
  Filter, 
  ChevronDown, 
  SlidersHorizontal, 
  Zap, 
  Pause, 
  Play 
} from 'lucide-react';

interface PipelineStatsHeaderProps {
  onOpenScaleModal: () => void;
  onForceFlush: () => void;
  selectedSource: string;
  onSelectSource: (source: string) => void;
}

export const PipelineStatsHeader: React.FC<PipelineStatsHeaderProps> = ({
  onOpenScaleModal,
  onForceFlush,
  selectedSource,
  onSelectSource,
}) => {
  const [isPaused, setIsPaused] = useState(false);
  const [isSourceOpen, setIsSourceOpen] = useState(false);

  const sources = [
    'Source: S3 + Confluence',
    'Source: All Providers (S3, Azure, GCS, Confluence)',
    'Source: s3://corp-legal-vault',
    'Source: confluence-prod-wiki',
    'Source: s3://financial-sec-filings',
  ];

  return (
    <div className="bg-[#0b101c] border-b border-slate-800/80 px-6 py-4 flex flex-wrap items-center justify-between gap-6 select-none">
      {/* Metrics Row */}
      <div className="flex flex-wrap items-center gap-8 lg:gap-12">
        {/* Metric 1: Ingested Today */}
        <div>
          <div className="text-[11px] uppercase tracking-wider font-semibold text-slate-400 font-mono mb-1">
            INGESTED TODAY
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white tracking-tight font-mono">
              4,819,420
            </span>
            <span className="text-xs font-semibold text-emerald-400 font-mono">
              +12.4% chunks
            </span>
          </div>
        </div>

        {/* Metric 2: In-Flight Pipeline */}
        <div>
          <div className="text-[11px] uppercase tracking-wider font-semibold text-slate-400 font-mono mb-1">
            IN-FLIGHT PIPELINE
          </div>
          <div className="flex items-baseline gap-1.5 font-mono">
            <span className="text-2xl font-bold text-white tracking-tight">
              14
            </span>
            <span className="text-xs text-slate-400 font-sans mr-1">batches</span>
            <span className="text-slate-600">/</span>
            <span className="text-sm font-semibold text-emerald-400">
              384
            </span>
            <span className="text-xs text-slate-400 font-sans">files</span>
          </div>
        </div>

        {/* Metric 3: Live Stream Throughput */}
        <div>
          <div className="text-[11px] uppercase tracking-wider font-semibold text-slate-400 font-mono mb-1">
            LIVE STREAM THROUGHPUT
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl font-bold text-emerald-400 font-mono tracking-tight">
              1,253
            </span>
            <span className="text-xs text-emerald-400 font-mono font-medium">
              items/s
            </span>
            <span className="text-xs text-slate-400 font-mono">
              (~48.2 MB/s)
            </span>
          </div>
        </div>

        {/* Metric 4: Fork Concurrency Gain */}
        <div>
          <div className="text-[11px] uppercase tracking-wider font-semibold text-slate-400 font-mono mb-1">
            FORK CONCURRENCY GAIN
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold text-white font-mono tracking-tight">
              2.14x
            </span>
            <span className="text-[10px] font-mono font-semibold text-purple-300 bg-purple-950/60 border border-purple-800/60 px-1.5 py-0.5 rounded tracking-wider">
              VECTOR || CLASS PARALLEL
            </span>
          </div>
        </div>
      </div>

      {/* Action Controls */}
      <div className="flex items-center gap-2.5">
        {/* Source Dropdown Filter */}
        <div className="relative">
          <button
            id="source-filter-btn"
            onClick={() => setIsSourceOpen(!isSourceOpen)}
            className="flex items-center gap-2 px-3 py-1.5 bg-[#121927] hover:bg-[#182235] border border-slate-800 rounded-md text-xs text-slate-200 font-mono transition-colors shadow-sm"
          >
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <span className="truncate max-w-[140px] text-left">{selectedSource}</span>
            <ChevronDown className="w-3 h-3 text-slate-400 ml-1" />
          </button>

          {isSourceOpen && (
            <div className="absolute right-0 mt-1.5 w-64 bg-[#0d1424] border border-slate-700/80 rounded-lg shadow-2xl py-1 z-40 text-xs font-mono">
              {sources.map((src) => (
                <button
                  key={src}
                  onClick={() => {
                    onSelectSource(src);
                    setIsSourceOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 hover:bg-blue-600/20 hover:text-blue-300 transition-colors ${
                    selectedSource === src ? 'text-blue-400 bg-blue-950/40 font-semibold' : 'text-slate-300'
                  }`}
                >
                  {src}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Scale Fleet Button */}
        <button
          id="scale-fleet-btn"
          onClick={onOpenScaleModal}
          className="flex items-center gap-2 px-3 py-1.5 bg-[#121927] hover:bg-[#182235] border border-slate-800 hover:border-slate-700 rounded-md text-xs text-slate-200 font-medium transition-colors shadow-sm"
        >
          <SlidersHorizontal className="w-3.5 h-3.5 text-emerald-400" />
          <span>Scale Fleet (64)</span>
        </button>

        {/* Force Flush Button */}
        <button
          id="force-flush-btn"
          onClick={onForceFlush}
          className="flex items-center gap-2 px-3 py-1.5 bg-[#121927] hover:bg-[#182235] border border-slate-800 hover:border-slate-700 rounded-md text-xs text-slate-200 font-medium transition-colors shadow-sm"
        >
          <Zap className="w-3.5 h-3.5 text-slate-400" />
          <span>Force Flush</span>
        </button>

        {/* Pause / Resume Ingestion Button */}
        <button
          id="pause-ingestion-btn"
          onClick={() => setIsPaused(!isPaused)}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
            isPaused
              ? 'bg-amber-600/30 border border-amber-500/60 text-amber-200 hover:bg-amber-600/40'
              : 'bg-[#1b2b4a] hover:bg-[#22365c] border border-blue-500/50 text-blue-200'
          }`}
        >
          {isPaused ? <Play className="w-3.5 h-3.5 fill-current" /> : <Pause className="w-3.5 h-3.5 fill-current" />}
          <span>{isPaused ? 'Resume Ingestion' : 'Pause Ingestion'}</span>
        </button>
      </div>
    </div>
  );
};
