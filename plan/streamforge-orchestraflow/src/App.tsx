import React, { useState, useEffect } from 'react';
import { TopNav } from './components/TopNav';
import { Sidebar } from './components/Sidebar';
import { PipelineStatsHeader } from './components/PipelineStatsHeader';
import { ActiveIngestionDag } from './components/ActiveIngestionDag';
import { BatchExecutionStream } from './components/BatchExecutionStream';
import { NodeDiagnosticPanel } from './components/NodeDiagnosticPanel';
import { JsonAstModal } from './components/JsonAstModal';
import { ScaleFleetModal } from './components/ScaleFleetModal';
import { 
  DAG_NODES, 
  INITIAL_BATCHES, 
  INITIAL_LOGS 
} from './data/mockPipelineData';
import { BatchItem, LogEntry } from './types';
import { CheckCircle2, AlertCircle } from 'lucide-react';

export default function App() {
  const [activeSidebarTab, setActiveSidebarTab] = useState('pipeline-orchestrator');
  const [selectedCluster, setSelectedCluster] = useState('production-us-east-1');
  const [isLive, setIsLive] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNodeId, setSelectedNodeId] = useState(4); // Node 4: Chunking (as in screenshot)
  const [selectedSource, setSelectedSource] = useState('Source: S3 + Confluence');
  const [workerCount, setWorkerCount] = useState(64);

  // Modals
  const [isAstModalOpen, setIsAstModalOpen] = useState(false);
  const [isScaleModalOpen, setIsScaleModalOpen] = useState(false);
  const [isRefreshingTail, setIsRefreshingTail] = useState(false);

  // Toast / notification
  const [notification, setNotification] = useState<string | null>(null);

  // Data states
  const [batches, setBatches] = useState<BatchItem[]>(INITIAL_BATCHES);
  const [logs, setLogs] = useState<LogEntry[]>(INITIAL_LOGS);

  const selectedNode = DAG_NODES.find((n) => n.id === selectedNodeId) || DAG_NODES[3];

  const showNotification = (msg: string) => {
    setNotification(msg);
    setTimeout(() => {
      setNotification(null);
    }, 3000);
  };

  // Live telemetry stream simulator
  useEffect(() => {
    if (!isLive) return;

    const interval = setInterval(() => {
      // Periodic subtle log addition
      const now = new Date();
      const timeStr = `${String(now.getUTCHours()).padStart(2, '0')}:${String(now.getUTCMinutes()).padStart(2, '0')}:${String(now.getUTCSeconds()).padStart(2, '0')}.${String(now.getUTCMilliseconds()).padStart(3, '0')}`;

      const randomEvents: { tag: string; tagColor: string; message: string }[] = [
        { tag: '[Branch A]', tagColor: 'text-emerald-400', message: `Vector embedding batch ${(Math.random() * 20 + 10).toFixed(0)}ms (GPU-Cluster-East)` },
        { tag: '[Branch B]', tagColor: 'text-purple-400', message: 'Token sequence boundary validated, 0 anomaly flags' },
        { tag: '[B-4820]', tagColor: 'text-slate-300', message: `Dispatched chunk packet #${Math.floor(Math.random() * 400 + 100)}` },
        { tag: '[Buffer]', tagColor: 'text-sky-400', message: 'Zero backpressure sustained across PCIe NVMe rings' }
      ];

      const sample = randomEvents[Math.floor(Math.random() * randomEvents.length)];

      setLogs((prev) => {
        const next = [...prev, { timestamp: timeStr, tag: sample.tag, tagColor: sample.tagColor, message: sample.message }];
        return next.slice(-9); // keep last 9 entries
      });
    }, 4500);

    return () => clearInterval(interval);
  }, [isLive]);

  // Refresh Tail handler
  const handleRefreshTail = () => {
    setIsRefreshingTail(true);
    setTimeout(() => {
      const now = new Date();
      const timeStr = `${String(now.getUTCHours()).padStart(2, '0')}:${String(now.getUTCMinutes()).padStart(2, '0')}:${String(now.getUTCSeconds()).padStart(2, '0')}.${String(now.getUTCMilliseconds()).padStart(3, '0')}`;
      
      setLogs((prev) => [
        ...prev,
        {
          timestamp: timeStr,
          tag: '[Tail-Sync]',
          tagColor: 'text-sky-400',
          message: 'Continuous buffer tail synchronized with origin master'
        }
      ].slice(-9));

      setIsRefreshingTail(false);
      showNotification('Tail logs refreshed successfully');
    }, 600);
  };

  // Force Flush handler
  const handleForceFlush = () => {
    showNotification('Flushing in-flight cache pipeline buffers to persistent storage...');
  };

  // Drain Buffer handler
  const handleDrainBuffer = () => {
    showNotification(`Buffer drained for ${selectedNode.name}. NVMe cache zeroed.`);
  };

  // Search filtering on batches
  const filteredBatches = batches.filter((b) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      b.id.toLowerCase().includes(query) ||
      b.source.toLowerCase().includes(query) ||
      b.filename.toLowerCase().includes(query) ||
      b.stageName.toLowerCase().includes(query)
    );
  });

  return (
    <div className="min-h-screen bg-[#070b13] text-slate-200 flex flex-col font-sans antialiased">
      {/* Toast Notification */}
      {notification && (
        <div className="fixed bottom-5 right-5 z-50 flex items-center gap-2.5 px-4 py-2.5 rounded-lg bg-blue-950/90 border border-blue-500/60 text-blue-200 text-xs font-mono shadow-2xl animate-in slide-in-from-bottom-3 duration-200">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{notification}</span>
        </div>
      )}

      {/* Top Navigation */}
      <TopNav
        isLive={isLive}
        onToggleLive={() => setIsLive(!isLive)}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        selectedCluster={selectedCluster}
        onChangeCluster={setSelectedCluster}
      />

      {/* Main Layout Body with Left Sidebar + Center Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <Sidebar
          activeTab={activeSidebarTab}
          onSelectTab={setActiveSidebarTab}
        />

        {/* Center Main Dashboard Content */}
        <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
          {/* Top Metrics & Action Buttons Bar */}
          <PipelineStatsHeader
            onOpenScaleModal={() => setIsScaleModalOpen(true)}
            onForceFlush={handleForceFlush}
            selectedSource={selectedSource}
            onSelectSource={setSelectedSource}
          />

          {/* Active Ingestion Graph (DAG) */}
          <ActiveIngestionDag
            nodes={DAG_NODES}
            selectedNodeId={selectedNodeId}
            onSelectNode={setSelectedNodeId}
          />

          {/* Bottom Split Section: Continuous Batch Execution Stream (Left) & Node Diagnostic (Right) */}
          <div className="p-6 grid grid-cols-1 xl:grid-cols-12 gap-6 bg-[#070b13]">
            {/* Continuous Batch Execution Stream (approx 7 cols) */}
            <div className="xl:col-span-7">
              <BatchExecutionStream
                batches={filteredBatches}
                onRefreshTail={handleRefreshTail}
                isRefreshing={isRefreshingTail}
                onSelectBatch={(id) => showNotification(`Inspecting batch ${id}`)}
              />
            </div>

            {/* Node Diagnostic Panel (approx 5 cols) */}
            <div className="xl:col-span-5">
              <NodeDiagnosticPanel
                selectedNode={selectedNode}
                logs={logs}
                onDrainBuffer={handleDrainBuffer}
                onOpenAstModal={() => setIsAstModalOpen(true)}
              />
            </div>
          </div>
        </main>
      </div>

      {/* Modals */}
      <JsonAstModal
        isOpen={isAstModalOpen}
        onClose={() => setIsAstModalOpen(false)}
        nodeName={selectedNode.name}
      />

      <ScaleFleetModal
        isOpen={isScaleModalOpen}
        onClose={() => setIsScaleModalOpen(false)}
        currentWorkers={workerCount}
        onUpdateWorkers={(val) => {
          setWorkerCount(val);
          showNotification(`Worker fleet scaled to ${val} parallel units.`);
        }}
      />
    </div>
  );
}
