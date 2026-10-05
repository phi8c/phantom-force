import { LoaderCircle, ShieldCheck } from "lucide-react";

export function AuthLoadingState() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-6">
      <div
        className="flex items-center gap-3 text-sm text-muted-foreground"
        role="status"
      >
        <span className="relative grid size-9 place-items-center rounded-lg border bg-card">
          <ShieldCheck className="size-4" />
          <LoaderCircle className="absolute -right-1 -top-1 size-3 animate-spin" />
        </span>
        Checking session...
      </div>
    </div>
  );
}
