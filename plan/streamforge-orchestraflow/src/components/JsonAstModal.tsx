import React, { useState } from 'react';
import { X, Copy, Check, FileCode2 } from 'lucide-react';
import { MOCK_JSON_AST } from '../data/mockPipelineData';

interface JsonAstModalProps {
  isOpen: boolean;
  onClose: () => void;
  nodeName: string;
}

export const JsonAstModal: React.FC<JsonAstModalProps> = ({ isOpen, onClose, nodeName }) => {
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const jsonString = JSON.stringify(MOCK_JSON_AST, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4 animate-in fade-in duration-150">
      <div className="bg-[#0b1120] border border-slate-700/80 rounded-xl w-full max-w-2xl overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-800 bg-[#0e1629]">
          <div className="flex items-center gap-2">
            <FileCode2 className="w-4 h-4 text-purple-400" />
            <h4 className="text-sm font-bold text-white font-mono">
              DAG Node AST Definition • {nodeName}
            </h4>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>

            <button
              onClick={onClose}
              className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* JSON Content */}
        <div className="p-4 max-h-[480px] overflow-y-auto bg-[#070a12] font-mono text-xs text-slate-200">
          <pre className="text-emerald-300/90 whitespace-pre-wrap leading-relaxed">
            {jsonString}
          </pre>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 bg-[#0e1629] border-t border-slate-800 flex justify-between items-center text-xs text-slate-400 font-mono">
          <span>Schema: dag-ast-v2.19.0-prod</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded font-medium text-xs transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
