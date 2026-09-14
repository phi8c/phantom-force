export interface DagNodeInfo {
  id: number;
  name: string;
  badge: string;
  badgeColor: 'green' | 'blue' | 'purple' | 'amber';
  subtitle: string;
  rateLabel: string;
  rateValue: string;
  metric2Label: string;
  metric2Value: string;
  metric2Color?: string;
  batchLabel: string;
  batchValue: string;
  description: string;
  nodeHealth: string;
  stat1Title: string;
  stat1Value: string;
  stat1Sub: string;
  stat2Title: string;
  stat2Value: string;
  stat2Sub: string;
}

export interface BatchItem {
  id: string;
  source: string;
  filename: string;
  payloadInfo: string;
  stageName: string;
  progressPercent: number;
  subtext: string;
  throughput: string;
  isForking?: boolean;
  parallelInfo?: {
    label: string;
    embedPercent: number;
    classifyPercent: number;
  };
}

export interface LogEntry {
  timestamp: string;
  tag: string;
  tagColor?: string;
  message: string;
  isReadySync?: boolean;
}
