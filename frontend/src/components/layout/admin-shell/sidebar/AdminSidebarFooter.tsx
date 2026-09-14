export function AdminSidebarFooter() {
  return (
    <div className="border-t p-3">
      <div className="flex items-center gap-3">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-muted text-sm font-medium">
          A
        </div>

        <div className="min-w-0 opacity-0 transition-opacity duration-150 group-hover:opacity-100">
          <p className="truncate text-sm font-medium">
            Administrator
          </p>

          <p className="truncate text-xs text-muted-foreground">
            Admin
          </p>
        </div>
      </div>
    </div>
  );
}