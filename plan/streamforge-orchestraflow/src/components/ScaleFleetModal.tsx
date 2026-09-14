import React, { useState } from 'react';
import { X, SlidersHorizontal, Cpu, CheckCircle } from 'lucide-react';

interface ScaleFleetModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentWorkers: number;
  onUpdateWorkers: (val: number) => void;
}

export const ScaleFleetModal: React.FC<ScaleFleetModalProps> = ({
  isOpen,
  onClose,
  currentWorkers,
  onUpdateWorkers,
}) => {
  const [workers, setWorkers] = useState(currentWorkers);

  if (!isOpen) return null;

  const presets = [16, 32, 64, 96, 128];

  const handleApply = () => {
    onUpdateWorkers(workers);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4 animate-in fade-in duration-150">
      <div className="bg-[#0b1120] border border-slate-700/80 rounded-xl w-full max-w-md overflow-hidden shadow-2xl">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800 bg-[#0e1629]">
          <div className="flex items-center gap-2.5">
            <SlidersHorizontal className="w-4 h-4 text-emerald-400" />
            <h4 className="text-sm font-bold text-white font-mono">
              Scale Worker Fleet
            </h4>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-6 space-y-5 text-xs font-mono">
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-slate-300 font-semibold">Active Parallel Workers:</span>
              <span className="text-lg font-bold text-emerald-400">{workers} / 128 max</span>
            </div>

            <input
              type="range"
              min="8"
              max="128"
              step="4"
              value={workers}
              onChange={(e) => setWorkers(Number(e.target.value))}
              className="w-full accent-emerald-500 cursor-pointer h-2 bg-slate-800 rounded-lg"
            />
          </div>

          <div>
            <span className="text-slate-400 block mb-2">Quick Presets:</span>
            <div className="grid grid-cols-5 gap-2">
              {presets.map((num) => (
                <button
                  key={num}
                  onClick={() => setWorkers(num)}
                  className={`py-1.5 rounded border text-center font-bold transition-colors ${
                    workers === num
                      ? 'bg-emerald-950/70 border-emerald-500 text-emerald-400'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {num}
                </button>
              ))}
            </div>
          </div>

          <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg space-y-1 text-slate-400 text-[11px]">
            <div className="flex items-center gap-1.5 text-slate-300">
              <Cpu className="w-3.5 h-3.5 text-sky-400" />
              <span>Auto-balancing active: zero packet loss guaranteed</span>
            </div>
            <p>Scaling updates DAG executor thread pool in ~400ms across cluster nodes.</p>
          </div>
        </div>

        <div className="px-5 py-3 bg-[#0e1629] border-t border-slate-800 flex justify-end gap-2 text-xs font-mono">
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleApply}
            className="px-4 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition-colors"
          >
            Apply Allocation
          </button>
        </div>
      </div>
    </div>
  );
};
