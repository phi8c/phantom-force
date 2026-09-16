"use client";

import { useEffect, useState } from "react";

import { BaseModal } from "@/components/shared/modal";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";

import { useCreateIngestionJob } from "../hooks/use-ingestion-config";

interface IngestionCreateDialogProps {
  open: boolean;
  knowledgeSpaceId?: string;
  onClose: () => void;
  onCreated: (ingestionJobId: string) => void;
}

export function IngestionCreateDialog({
  open,
  knowledgeSpaceId,
  onClose,
  onCreated,
}: IngestionCreateDialogProps) {
  const [isBuildGraph, setIsBuildGraph] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const createMutation = useCreateIngestionJob();

  useEffect(() => {
    if (!open) {
      return;
    }

    setIsBuildGraph(false);
    setError(null);
  }, [open]);

  async function handleCreate() {
    if (!knowledgeSpaceId) {
      setError("Knowledge Space context is required.");
      return;
    }

    setError(null);

    try {
      const result = await createMutation.mutateAsync({
        knowledgeSpaceId,
        triggerType: "MANUAL",
        isBuildGraph,
      });

      onCreated(result.ingestion_job_id);
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Unable to create ingestion job.",
      );
    }
  }

  return (
    <BaseModal
      open={open}
      onOpenChange={(nextOpen) => {
        if (!nextOpen && !createMutation.isPending) {
          onClose();
        }
      }}
      title="Create Ingestion"
      description={knowledgeSpaceId}
      size="lg"
      preventClose={createMutation.isPending}
      footer={
        <>
          <Button
            type="button"
            variant="outline"
            disabled={createMutation.isPending}
            onClick={onClose}
          >
            Cancel
          </Button>

          <Button
            type="button"
            disabled={
              !knowledgeSpaceId || createMutation.isPending
            }
            onClick={() => void handleCreate()}
          >
            {createMutation.isPending ? "Creating..." : "Create"}
          </Button>
        </>
      }
    >
      <div className="grid gap-4">
        <div className="grid gap-2">
          <Label>Trigger Type</Label>
          <div className="flex h-9 items-center rounded-lg border px-3 text-sm">
            MANUAL
          </div>
        </div>

        <div className="flex items-center justify-between rounded-lg border px-3 py-2">
          <Label>Build Knowledge Graph</Label>
          <Switch
            checked={isBuildGraph}
            onCheckedChange={setIsBuildGraph}
          />
        </div>

        {error && (
          <p className="text-sm text-destructive">
            {error}
          </p>
        )}
      </div>
    </BaseModal>
  );
}
