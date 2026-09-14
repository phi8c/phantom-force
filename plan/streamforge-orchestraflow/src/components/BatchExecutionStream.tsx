import React from 'react';
import { 
  Layers, 
  RotateCw, 
  ChevronLeft, 
  ChevronRight,
  FileText
} from 'lucide-react';
import { BatchItem } from '../types';

interface BatchExecutionStreamProps {
  batches: BatchItem[];
  onRefreshTail: () => void;
  isRefreshing: boolean;
  onSelectBatch?: (batchId: string) => void;
}

export const BatchExecutionStream: React.FC<BatchExecutionStreamProps> = ({
  batches,
  onRefreshTail,
  isRefreshing,
  onSelectBatch
}) => {
  return (
    <div className="bg-[#0b101c] border border-slate-800/80 rounded-lg flex flex-col justify-between overflow-hidden shadow-sm">
      {/* Header */}
      <div className="px-5 py-3 border-b border-slate-800/80 flex items-center justify-between bg-[#0e1424]/50">
        <div className="flex items-center gap-3">
          <Layers className="w-4 h-4 text-blue-400" />
          <h3 className="text-sm font-bold text-white tracking-tight font-sans">
            Continuous Batch Execution Stream
          </h3>
          <span className="text-[11px] font-mono text-slate-300 bg-slate-800/80 border border-slate-700/60 px-2 py-0.5 rounded-full">
            5 Active Batches
          </span>
        </div>

        <button
          id="refresh-tail-btn"
          onClick={onRefreshTail}
          className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono text-slate-300 hover:text-white bg-[#121927] hover:bg-slate-800 border border-slate-800 hover:border-slate-700 rounded transition-all"
        >
          <RotateCw className={`w-3 h-3 text-slate-400 ${isRefreshing ? 'animate-spin text-blue-400' : ''}`} />
          <span>Refresh Tail</span>
        </button>
      </div>

      {/* Batches Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse font-mono text-xs">
          <thead>
            <tr className="border-b border-slate-800/70 text-[11px] uppercase tracking-wider text-slate-400 bg-[#090e1a]/60">
              <th className="py-2.5 px-5 font-semibold">BATCH ID & SOURCE</th>
              <th className="py-2.5 px-5 font-semibold">IN-FLIGHT FILE PAYLOAD</th>
              <th className="py-2.5 px-5 font-semibold">STAGE PROGRESS FLOW</th>
              <th className="py-2.5 px-5 font-semibold text-right">THROUGHPUT</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {batches.map((batch) => (
              <tr 
                key={batch.id} 
                onClick={() => onSelectBatch && onSelectBatch(batch.id)}
                className="hover:bg-slate-850/40 hover:bg-[#11182c]/60 transition-colors cursor-pointer group"
              >
                {/* Col 1: Batch ID & Source */}
                <td className="py-3 px-5 align-top whitespace-nowrap">
                  <div className="font-bold text-slate-100 group-hover:text-blue-400 transition-colors">
                    {batch.id}
                  </div>
                  <div className="text-[11px] text-slate-400 font-normal">
                    {batch.source}
                  </div>
                </td>

                {/* Col 2: In-Flight Payload */}
                <td className="py-3 px-5 align-top">
                  <div className="text-slate-200 font-medium text-xs break-all">
                    {batch.filename}
                  </div>
                  <div className="text-[11px] text-slate-400 font-normal">
                    {batch.payloadInfo}
                  </div>
                </td>

                {/* Col 3: Stage Progress Flow */}
                <td className="py-3 px-5 align-top min-w-[240px]">
                  {batch.isForking && batch.parallelInfo ? (
                    <div>
                      {/* Forking stage with 2 parallel branches */}
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-emerald-400 font-semibold">
                          {batch.stageName}
                        </span>
                        <span className="text-slate-300 font-medium">
                          {batch.parallelInfo.label}
                        </span>
                      </div>

                      {/* Dual Progress Bar for Embed & Classify */}
                      <div className="grid grid-cols-2 gap-2 mt-1.5">
                        {/* Embed Branch Bar */}
                        <div>
                          <div className="flex items-center justify-between text-[10px] text-slate-400 mb-0.5">
                            <span>Embed:</span>
                            <span className="text-cyan-400 font-semibold">{batch.parallelInfo.embedPercent}%</span>
                          </div>
                          <div className="w-full bg-slate-800/80 h-1.5 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-gradient-to-r from-cyan-500 to-sky-400 rounded-full transition-all duration-500" 
                              style={{ width: `${batch.parallelInfo.embedPercent}%` }}
                            />
                          </div>
                        </div>

                        {/* Classify Branch Bar */}
                        <div>
                          <div className="flex items-center justify-between text-[10px] text-slate-400 mb-0.5">
                            <span>Classify:</span>
                            <span className="text-emerald-400 font-semibold">{batch.parallelInfo.classifyPercent}%</span>
                          </div>
                          <div className="w-full bg-slate-800/80 h-1.5 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-500" 
                              style={{ width: `${batch.parallelInfo.classifyPercent}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div>
                      {/* Standard stage with single progress bar */}
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-slate-200 font-medium">
                          {batch.stageName}
                        </span>
                        <span className="text-slate-300 font-semibold">
                          {batch.progressPercent}%
                        </span>
                      </div>

                      <div className="w-full bg-slate-800/80 h-1.5 rounded-full overflow-hidden mt-1">
                        <div 
                          className="h-full bg-gradient-to-r from-blue-600 via-sky-500 to-cyan-400 rounded-full transition-all duration-500" 
                          style={{ width: `${batch.progressPercent}%` }}
                        />
                      </div>

                      {batch.subtext && (
                        <div className="text-[10px] text-slate-400 mt-1">
                          {batch.subtext}
                        </div>
                      )}
                    </div>
                  )}
                </td>

                {/* Col 4: Throughput */}
                <td className="py-3 px-5 align-top text-right whitespace-nowrap">
                  <span className="text-slate-200 font-semibold">
                    {batch.throughput}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="px-5 py-2.5 border-t border-slate-800/80 bg-[#090e1a]/60 flex flex-wrap items-center justify-between gap-3 text-xs font-mono text-slate-400">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400" />
          <span>Contiguous sliding batch window: 24 active slots remaining</span>
        </div>

        <div className="flex items-center gap-3">
          <span>Showing live sliding 5 of 14 batches</span>
          <div className="flex items-center gap-1">
            <button 
              id="prev-batch-page-btn"
              className="p-1 rounded bg-[#121927] hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 transition-colors"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            <button 
              id="next-batch-page-btn"
              className="p-1 rounded bg-[#121927] hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 transition-colors"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
