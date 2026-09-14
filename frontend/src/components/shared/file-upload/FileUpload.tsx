"use client";

import {
  FileArchive,
  FileAudio,
  FileImage,
  FileText,
  FileVideo,
  File as FileIcon,
  Upload,
  X,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { FileUploadPreview } from "./FileUploadPreview";

interface FileUploadProps {
  multiple?: boolean;
  accept?: string[];
  maxFiles?: number;
  maxSize?: number;
  disabled?: boolean;
  onFilesChange?: (files: File[]) => void;
  className?: string;
}

export function FileUpload({
  multiple = false,
  accept,
  maxFiles,
  maxSize,
  disabled = false,
  onFilesChange,
  className,
}: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateFiles = useCallback(
    (nextFiles: File[]) => {
      setFiles(nextFiles);
      onFilesChange?.(nextFiles);
    },
    [onFilesChange],
  );

  const validateFile = useCallback(
    (file: File): string | null => {
      if (maxSize && file.size > maxSize) {
        return `"${file.name}" exceeds the maximum file size of ${formatFileSize(
          maxSize,
        )}.`;
      }

      if (accept && accept.length > 0) {
        const extension = `.${file.name.split(".").pop()?.toLowerCase()}`;
        const mimeType = file.type.toLowerCase();

        const isAccepted = accept.some((type) => {
          const normalizedType = type.toLowerCase();

          if (normalizedType.startsWith(".")) {
            return normalizedType === extension;
          }

          if (normalizedType.endsWith("/*")) {
            return mimeType.startsWith(
              normalizedType.replace("/*", "/"),
            );
          }

          return normalizedType === mimeType;
        });

        if (!isAccepted) {
          return `"${file.name}" is not a supported file type.`;
        }
      }

      return null;
    },
    [accept, maxSize],
  );

  const handleFiles = useCallback(
    (incomingFiles: File[]) => {
      if (disabled || incomingFiles.length === 0) {
        return;
      }

      setError(null);

      const validFiles: File[] = [];

      for (const file of incomingFiles) {
        const validationError = validateFile(file);

        if (validationError) {
          setError(validationError);
          continue;
        }

        validFiles.push(file);
      }

      if (validFiles.length === 0) {
        return;
      }

      let nextFiles: File[];

      if (!multiple) {
        nextFiles = [validFiles[0]];
      } else {
        const existingKeys = new Set(
          files.map((file) => createFileKey(file)),
        );

        const uniqueFiles = validFiles.filter(
          (file) => !existingKeys.has(createFileKey(file)),
        );

        nextFiles = [...files, ...uniqueFiles];
      }

      if (maxFiles && nextFiles.length > maxFiles) {
        nextFiles = nextFiles.slice(0, maxFiles);

        setError(`You can select up to ${maxFiles} files.`);
      }

      updateFiles(nextFiles);
    },
    [
      disabled,
      files,
      maxFiles,
      multiple,
      updateFiles,
      validateFile,
    ],
  );

  const handleInputChange = (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const selectedFiles = Array.from(event.target.files ?? []);

    handleFiles(selectedFiles);

    // Allows selecting the same file again.
    event.target.value = "";
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();

    if (disabled) {
      return;
    }

    setIsDragging(false);

    const droppedFiles = Array.from(event.dataTransfer.files);

    handleFiles(droppedFiles);
  };

  const handleRemove = (file: File) => {
    const nextFiles = files.filter(
      (item) => createFileKey(item) !== createFileKey(file),
    );

    setError(null);
    updateFiles(nextFiles);
  };

  const handleClear = () => {
    setError(null);
    updateFiles([]);
  };

  useEffect(() => {
    return () => {
      // Preview components own their object URLs.
    };
  }, []);

  return (
    <div className={cn("space-y-4", className)}>
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        onClick={() => {
          if (!disabled) {
            inputRef.current?.click();
          }
        }}
        onKeyDown={(event) => {
          if (
            !disabled &&
            (event.key === "Enter" || event.key === " ")
          ) {
            event.preventDefault();
            inputRef.current?.click();
          }
        }}
        onDragEnter={(event) => {
          event.preventDefault();

          if (!disabled) {
            setIsDragging(true);
          }
        }}
        onDragOver={(event) => {
          event.preventDefault();

          if (!disabled) {
            setIsDragging(true);
          }
        }}
        onDragLeave={(event) => {
          event.preventDefault();

          if (event.currentTarget === event.target) {
            setIsDragging(false);
          }
        }}
        onDrop={handleDrop}
        className={cn(
          "flex min-h-40 cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 text-center transition-colors",
          "border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/30",
          isDragging && "border-primary bg-primary/5",
          disabled &&
            "cursor-not-allowed opacity-50 hover:border-muted-foreground/25 hover:bg-transparent",
        )}
      >
        <input
          ref={inputRef}
          type="file"
          multiple={multiple}
          accept={accept?.join(",")}
          disabled={disabled}
          className="hidden"
          onChange={handleInputChange}
        />

        <div className="mb-3 flex size-11 items-center justify-center rounded-full bg-muted">
          <Upload className="size-5 text-muted-foreground" />
        </div>

        <p className="text-sm font-medium">
          {isDragging
            ? "Drop files here"
            : "Drag & drop files here"}
        </p>

        <p className="mt-1 text-xs text-muted-foreground">
          or click to browse from your computer
        </p>

        {accept && accept.length > 0 && (
          <p className="mt-3 text-xs text-muted-foreground">
            Supported: {accept.join(", ")}
          </p>
        )}

        {maxSize && (
          <p className="mt-1 text-xs text-muted-foreground">
            Maximum size: {formatFileSize(maxSize)}
          </p>
        )}
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/20 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {files.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">
                Selected files
              </p>

              <p className="text-xs text-muted-foreground">
                {files.length} {files.length === 1 ? "file" : "files"}
              </p>
            </div>

            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={handleClear}
              disabled={disabled}
            >
              Clear all
            </Button>
          </div>

          <div className="grid gap-3">
            {files.map((file) => (
              <FileUploadPreview
                key={createFileKey(file)}
                file={file}
                onRemove={handleRemove}
                disabled={disabled}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function createFileKey(file: File): string {
  return `${file.name}-${file.size}-${file.lastModified}`;
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

export function getFileIcon(file: File) {
  if (file.type.startsWith("image/")) {
    return FileImage;
  }

  if (file.type.startsWith("video/")) {
    return FileVideo;
  }

  if (file.type.startsWith("audio/")) {
    return FileAudio;
  }

  if (
    file.type === "application/pdf" ||
    file.type.includes("word") ||
    file.type.includes("text")
  ) {
    return FileText;
  }

  if (
    file.type.includes("zip") ||
    file.type.includes("rar") ||
    file.type.includes("compressed")
  ) {
    return FileArchive;
  }

  return FileIcon;
}