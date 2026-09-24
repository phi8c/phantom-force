"use client";

import { DataHubTree } from "@/modules/data-hub";

import type { IngestionScopeRoot } from "../../types/ingestion.types";

interface SourceScopeStepProps {
  knowledgeSpaceId?: string;
  selectedRoots: IngestionScopeRoot[];
  onSelectedRootsChange: (roots: IngestionScopeRoot[]) => void;
}

export function SourceScopeStep({
  knowledgeSpaceId,
  selectedRoots,
  onSelectedRootsChange,
}: SourceScopeStepProps) {
  if (!knowledgeSpaceId) {
    return (
      <p className="rounded-md border border-destructive/30 px-3 py-4 text-sm text-destructive">
        A Knowledge Space is required to browse Data Hub sources.
      </p>
    );
  }

  return (
    <div className="grid gap-3">
      <DataHubTree
        knowledgeSpaceId={knowledgeSpaceId}
        selectedRoots={selectedRoots}
        onSelectedRootsChange={onSelectedRootsChange}
      />

      <div className="rounded-lg bg-muted/50 px-3 py-2 text-xs text-muted-foreground">
        {selectedRoots.length} root
        {selectedRoots.length === 1 ? "" : "s"} selected
      </div>
    </div>
  );
}
