"use client";

import { Download, ExternalLink, X } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { getFileIcon } from "./FileUpload";

interface FileUploadPreviewProps {
  file: File;
  onRemove: (file: File) => void;
  disabled?: boolean;
}

export function FileUploadPreview({
  file,
  onRemove,
  disabled = false,
}: FileUploadPreviewProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const isImage = file.type.startsWith("image/");
  const isPdf = file.type === "application/pdf";

  useEffect(() => {
    const url = URL.createObjectURL(file);

    setPreviewUrl(url);

    return () => {
      URL.revokeObjectURL(url);
    };
  }, [file]);

  const Icon = getFileIcon(file);

  if (isImage && previewUrl) {
    return (
      <div className="overflow-hidden rounded-xl border bg-card">
        <div className="relative aspect-video w-full overflow-hidden bg-muted">
          <img
            src={previewUrl}
            alt={file.name}
            className="size-full object-contain"
          />

          <Button
            type="button"
            variant="secondary"
            size="icon"
            className="absolute right-2 top-2 size-8"
            onClick={() => onRemove(file)}
            disabled={disabled}
            aria-label={`Remove ${file.name}`}
          >
            <X />
          </Button>
        </div>

        <div className="p-3">
          <p className="truncate text-sm font-medium">{file.name}</p>

          <p className="text-xs text-muted-foreground">
            {formatFileSize(file.size)}
          </p>
        </div>
      </div>
    );
  }

  if (isPdf && previewUrl) {
    return (
      <div className="overflow-hidden rounded-xl border bg-card">
        <div className="relative h-80 w-full overflow-hidden bg-muted">
          <iframe
            src={previewUrl}
            title={file.name}
            className="size-full border-0"
          />

          <Button
            type="button"
            variant="secondary"
            size="icon"
            className="absolute right-2 top-2 size-8"
            onClick={() => onRemove(file)}
            disabled={disabled}
            aria-label={`Remove ${file.name}`}
          >
            <X />
          </Button>
        </div>

        <div className="flex items-center justify-between gap-3 p-3">
          <div className="min-w-0">
            <p className="truncate text-sm font-medium">{file.name}</p>

            <p className="text-xs text-muted-foreground">
              {formatFileSize(file.size)}
            </p>
          </div>

          <a
            href={previewUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex shrink-0 items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground"
          >
            <ExternalLink className="size-3.5" />
            Open
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 rounded-xl border bg-card p-3">
      <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-muted">
        <Icon className="size-5 text-muted-foreground" />
      </div>

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{file.name}</p>

        <p className="text-xs text-muted-foreground">
          {formatFileSize(file.size)}
        </p>
      </div>

      <a
        href={previewUrl ?? "#"}
        download={file.name}
        className={cn(
          "shrink-0",
          !previewUrl && "pointer-events-none opacity-50",
        )}
        aria-label={`Download ${file.name}`}
      >
        <span className="inline-flex">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            tabIndex={-1}
          >
            <Download />
          </Button>
        </span>
      </a>

      <Button
        type="button"
        variant="ghost"
        size="icon"
        onClick={() => onRemove(file)}
        disabled={disabled}
        aria-label={`Remove ${file.name}`}
      >
        <X />
      </Button>
    </div>
  );
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) {
    return "0 Bytes";
  }

  const units = ["Bytes", "KB", "MB", "GB"];

  const unitIndex = Math.floor(
    Math.log(bytes) / Math.log(1024),
  );

  const value = bytes / Math.pow(1024, unitIndex);

  return `${value.toFixed(unitIndex === 0 ? 0 : 1)} ${
    units[unitIndex] ?? "GB"
  }`;
}