import { DagNodeInfo, BatchItem, LogEntry } from '../types';

export const DAG_NODES: DagNodeInfo[] = [
  {
    id: 1,
    name: '1. Discovery',
    badge: 'ACTIVE',
    badgeColor: 'green',
    subtitle: 'S3 • Azure • Confluence API',
    rateLabel: 'Rate:',
    rateValue: '240 files/min',
    metric2Label: 'Discovered:',
    metric2Value: '1,482 pending',
    metric2Color: 'text-emerald-400',
    batchLabel: 'Batch #B-4824',
    batchValue: '42 scanned',
    description: 'Continuously polls and discovers file updates via change feeds, enterprise webhooks, and bucket lifecycle event notifications.',
    nodeHealth: 'HEALTHY (0.00% Err)',
    stat1Title: 'DISCOVERY LAG',
    stat1Value: '210ms',
    stat1Sub: 'Event queue empty',
    stat2Title: 'WATCHED SOURCES',
    stat2Value: '18 Roots',
    stat2Sub: 'Delta hash verified'
  },
  {
    id: 2,
    name: '2. Download',
    badge: 'STREAM',
    badgeColor: 'blue',
    subtitle: 'Streaming Blob Cache',
    rateLabel: 'Throughput:',
    rateValue: '64.5 MB/s',
    metric2Label: 'IO Buffer:',
    metric2Value: '99.8% hit',
    metric2Color: 'text-emerald-400',
    batchLabel: 'Batch #B-4823',
    batchValue: '18/24 blobs',
    description: 'Pulls binary payloads from distributed object stores straight into high-speed NVMe memory caches with zero local disk write amplification.',
    nodeHealth: 'HEALTHY (0.02% Err)',
    stat1Title: 'INGRESS LATENCY',
    stat1Value: '18.4ms',
    stat1Sub: 'Direct pipe stream',
    stat2Title: 'MEMORY BUFFER',
    stat2Value: '128 GB',
    stat2Sub: 'L1 PCIe NVMe'
  },
  {
    id: 3,
    name: '3. Extraction',
    badge: 'PARSER',
    badgeColor: 'green',
    subtitle: 'PDF • DOCX • HTML • OCR',
    rateLabel: 'Avg Parse:',
    rateValue: '68ms/doc',
    metric2Label: 'Lossless:',
    metric2Value: '100.0%',
    metric2Color: 'text-emerald-400',
    batchLabel: 'Batch #B-4822',
    batchValue: '32/32 files',
    description: 'Applies deterministic document decoders, layout detection, table structure extraction, and OCR pipelines to output clean structural Markdown.',
    nodeHealth: 'HEALTHY (0.00% Err)',
    stat1Title: 'OCR LATENCY',
    stat1Value: '68ms',
    stat1Sub: 'CPU SIMD accelerated',
    stat2Title: 'LOSSLESS PURITY',
    stat2Value: '100%',
    stat2Sub: 'DOM ast preserved'
  },
  {
    id: 4,
    name: '4. Chunking',
    badge: 'SPLIT',
    badgeColor: 'purple',
    subtitle: 'Semantic • 512 tok + 15%...',
    rateLabel: 'Output Rate:',
    rateValue: '1,248 ch/s',
    metric2Label: 'Parallel Fork:',
    metric2Value: '2 Branches',
    batchLabel: 'Batch #B-4821',
    batchValue: '512 chunks',
    description: 'Performs sentence-boundary recursive character chunking with dynamic token sizing, then dispatches chunk arrays asynchronously to Branch A (Embedding) and Branch B (Classification) simultaneously.',
    nodeHealth: 'HEALTHY (0.01% Err)',
    stat1Title: 'FORK DISPATCH LATENCY',
    stat1Value: '1.4ms',
    stat1Sub: 'Zero-queue lock',
    stat2Title: 'EMBEDDING VECTORS',
    stat2Value: '3,072-dim',
    stat2Sub: 'Cosine Distance'
  }
];

export const INITIAL_BATCHES: BatchItem[] = [
  {
    id: '#B-4820',
    source: 's3://corp-legal-vault',
    filename: 'global_settlement_agreement_2024.pdf',
    payloadInfo: '14.8 MB • 82 pgs • 340 chunks',
    stageName: 'Chunking Done → Forking',
    progressPercent: 88,
    subtext: '',
    throughput: '184 ch/s',
    isForking: true,
    parallelInfo: {
      label: 'Parallel 88%',
      embedPercent: 92,
      classifyPercent: 84
    }
  },
  {
    id: '#B-4821',
    source: 'confluence-prod-wiki',
    filename: 'q3_financial_risk_architecture.docx',
    payloadInfo: '4.2 MB • 24 pgs • 118 chunks',
    stageName: 'Stage 4: Chunking',
    progressPercent: 68,
    subtext: 'Tokenizing 512w w/ 15% overlap',
    throughput: '92 ch/s'
  },
  {
    id: '#B-4822',
    source: 's3://financial-sec-filings',
    filename: '10k_annual_filing_stream.html',
    payloadInfo: '8.9 MB • Table & DOM extraction',
    stageName: 'Stage 3: Extraction',
    progressPercent: 42,
    subtext: 'HTML DOM parser & markdown strip',
    throughput: '31 MB/s'
  },
  {
    id: '#B-4823',
    source: 'gcs://user-knowledge-base',
    filename: 'support_ticket_telemetry_dump.json',
    payloadInfo: '104.2 MB • Streamed Ephemeral',
    stageName: 'Stage 2: Download',
    progressPercent: 79,
    subtext: 'Streaming into SSD NVMe buffer',
    throughput: '88 MB/s'
  },
  {
    id: '#B-4824',
    source: 'sharepoint-enterprise-api',
    filename: 'hr_policies_compensation_v2.pdf',
    payloadInfo: 'Scanning incremental delta changes',
    stageName: 'Stage 1: Discovery',
    progressPercent: 15,
    subtext: 'Change feed diff timestamp matched',
    throughput: '12 items/s'
  }
];

export const INITIAL_LOGS: LogEntry[] = [
  {
    timestamp: '14:02:17.102',
    tag: '[B-4820]',
    tagColor: 'text-slate-300',
    message: 'Chunk window 0.512 generated'
  },
  {
    timestamp: '14:02:17.214',
    tag: '[Branch A]',
    tagColor: 'text-emerald-400',
    message: 'Dispatched 340 chunks to GPU-Cluster-East'
  },
  {
    timestamp: '14:02:17.215',
    tag: '[Branch B]',
    tagColor: 'text-purple-400',
    message: 'PII classifier initialized regex + RoBERTa'
  },
  {
    timestamp: '14:02:17.480',
    tag: '[Branch A]',
    tagColor: 'text-emerald-400',
    message: 'Batch vectorization complete (24ms)'
  },
  {
    timestamp: '14:02:17.510',
    tag: '[Branch B]',
    tagColor: 'text-purple-400',
    message: '0 PII violations found. 4 tags added'
  },
  {
    timestamp: '14:02:18.012',
    tag: '[B-4821]',
    tagColor: 'text-slate-300',
    message: "Tokenizing document 'q3_financial_risk.docx'"
  },
  {
    timestamp: '14:02:18.420',
    tag: '',
    message: 'Ready for downstream index sync',
    isReadySync: true
  }
];

export const MOCK_JSON_AST = {
  $schema: "https://streamforge.io/schemas/dag-ast-v2.json",
  pipeline_id: "pipe-orchestraflow-prod-east1",
  version: "dag-v2.19.0-prod",
  status: "ACTIVE_CONTIGUOUS",
  active_node: {
    id: "stage-04-chunking-router",
    type: "SentenceBoundaryRecursiveSplitter",
    config: {
      chunk_size_tokens: 512,
      overlap_percentage: 15.0,
      separators: ["\n\n", "\n", ". ", "? ", "! "],
      keep_separator: true
    },
    fork_dispatch: {
      mode: "INDEPENDENT_NON_BLOCKING",
      channels: [
        {
          branch: "Branch A (Embedding)",
          target_pool: "GPU-Cluster-East",
          dimensions: 3072,
          metric: "cosine",
          batch_size: 64
        },
        {
          branch: "Branch B (Classification)",
          model: "RoBERTa-PII-v4",
          scrub_pii: false,
          tag_injection: true
        }
      ]
    },
    telemetry: {
      uptime_seconds: 489218,
      total_dispatched_chunks: 5821940,
      error_rate: 0.0001,
      avg_latency_ms: 1.4
    }
  }
};
