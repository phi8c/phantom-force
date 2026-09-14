import { AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";

interface ErrorStateProps {
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function ErrorState({
  title = "Something went wrong",
  description = "We are unable to process your request right now. Please try again later.",
  actionLabel = "Try again",
  onAction,
}: ErrorStateProps) {
  return (
    <div className="flex min-h-[400px] items-center justify-center p-6">
      <div className="flex max-w-md flex-col items-center text-center">
        <div className="mb-4 flex size-12 items-center justify-center rounded-full bg-destructive/10 text-destructive">
          <AlertTriangle className="size-6" />
        </div>

        <h2 className="text-lg font-semibold tracking-tight">
          {title}
        </h2>

        <p className="mt-2 text-sm leading-6 text-muted-foreground">
          {description}
        </p>

        {onAction && (
          <Button
            type="button"
            variant="outline"
            className="mt-5"
            onClick={onAction}
          >
            {actionLabel}
          </Button>
        )}
      </div>
    </div>
  );
}