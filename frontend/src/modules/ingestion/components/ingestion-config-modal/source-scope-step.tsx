"use client";

import { DataHubTree } from "@/modules/data-hub";

import type { IngestionScopeRoot } from "../../types/ingestion.types";

interface SourceScopeStepProps {
  selectedRoots: IngestionScopeRoot[];
  onSelectedRootsChange: (roots: IngestionScopeRoot[]) => void;
}

export function SourceScopeStep({
  selectedRoots,
  onSelectedRootsChange,
}: SourceScopeStepProps) {
  return (
    <div className="grid gap-3">
      <DataHubTree
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
