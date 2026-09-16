"use client";

import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";

import type { IngestionMasterOption } from "../../types/ingestion.types";

interface ProcessingStepProps {
  extractionEngineCode: string;
  chunkingStrategyCode: string;
  classification: boolean;
  configurationText: string;
  loading: boolean;
  extractionEngines: IngestionMasterOption[];
  chunkingStrategies: IngestionMasterOption[];
  onExtractionEngineChange: (code: string) => void;
  onChunkingStrategyChange: (code: string) => void;
  onClassificationChange: (checked: boolean) => void;
  onConfigurationTextChange: (value: string) => void;
}

export function ProcessingStep({
  extractionEngineCode,
  chunkingStrategyCode,
  classification,
  configurationText,
  loading,
  extractionEngines,
  chunkingStrategies,
  onExtractionEngineChange,
  onChunkingStrategyChange,
  onClassificationChange,
  onConfigurationTextChange,
}: ProcessingStepProps) {
  return (
    <div className="grid gap-4">
      <div className="grid gap-2">
        <Label>Extraction Engine</Label>
        <Select
          value={extractionEngineCode}
          onValueChange={(value) =>
            onExtractionEngineChange(value ?? "")
          }
          disabled={loading}
        >
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {extractionEngines.map((engine) => (
              <SelectItem
                key={engine.id}
                value={engine.code}
              >
                {engine.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid gap-2">
        <Label>Chunking Strategy</Label>
        <Select
          value={chunkingStrategyCode}
          onValueChange={(value) =>
            onChunkingStrategyChange(value ?? "")
          }
          disabled={loading}
        >
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {chunkingStrategies.map((strategy) => (
              <SelectItem
                key={strategy.id}
                value={strategy.code}
              >
                {strategy.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex items-center justify-between rounded-lg border px-3 py-2">
        <div>
          <Label>Classification</Label>
        </div>
        <Switch
          checked={classification}
          onCheckedChange={onClassificationChange}
          disabled={loading}
        />
      </div>

      <div className="grid gap-2">
        <Label>Configuration</Label>
        <Textarea
          value={configurationText}
          rows={8}
          className="font-mono text-sm"
          onChange={(event) =>
            onConfigurationTextChange(event.target.value)
          }
        />
      </div>
    </div>
  );
}
