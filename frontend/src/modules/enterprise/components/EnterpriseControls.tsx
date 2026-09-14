"use client";

import { Plus, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";

interface EnterpriseControlsProps {
  loading?: boolean;
  onCreate: () => void;
  onRefresh: () => void;
}

export function EnterpriseControls({
  loading = false,
  onCreate,
  onRefresh,
}: EnterpriseControlsProps) {
  return (
    <div className="flex items-center justify-between border-b px-6 py-3">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">
          Enterprises
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage organizations that contain knowledge spaces.
        </p>
      </div>

      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="outline"
          size="icon"
          disabled={loading}
          onClick={onRefresh}
          aria-label="Refresh enterprises"
          title="Refresh"
        >
          <RefreshCw className="size-4" />
        </Button>

        <Button
          type="button"
          onClick={onCreate}
        >
          <Plus className="size-4" />
          New enterprise
        </Button>
      </div>
    </div>
  );
}
