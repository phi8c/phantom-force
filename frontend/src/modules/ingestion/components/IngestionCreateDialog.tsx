"use client";

import { useState } from "react";
import { X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface IngestionCreateDialogProps {
  open: boolean;
  onClose: () => void;
}

export function IngestionCreateDialog({
  open,
  onClose,
}: IngestionCreateDialogProps) {
  const [name, setName] = useState("");

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-lg rounded-xl border bg-background shadow-xl">
        <div className="flex items-center justify-between border-b px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold">
              New ingestion
            </h2>

            <p className="mt-1 text-sm text-muted-foreground">
              Create a new ingestion job.
            </p>
          </div>

          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={onClose}
          >
            <X className="size-4" />
          </Button>
        </div>

        <div className="space-y-4 px-6 py-5">
          <div className="space-y-2">
            <label
              htmlFor="ingestion-name"
              className="text-sm font-medium"
            >
              Ingestion name
            </label>

            <Input
              id="ingestion-name"
              value={name}
              onChange={(event) =>
                setName(event.target.value)
              }
              placeholder="Enter ingestion name"
            />
          </div>

          <div className="rounded-lg bg-muted/50 p-3 text-sm text-muted-foreground">
            Source and Knowledge Space selection will be
            connected to backend data later.
          </div>
        </div>

        <div className="flex justify-end gap-2 border-t px-6 py-4">
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
          >
            Cancel
          </Button>

          <Button
            type="button"
            disabled={!name.trim()}
            onClick={onClose}
          >
            Create
          </Button>
        </div>
      </div>
    </div>
  );
}