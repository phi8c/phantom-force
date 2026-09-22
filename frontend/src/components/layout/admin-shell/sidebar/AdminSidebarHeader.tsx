import Link from "next/link";

export function AdminSidebarHeader() {
  return (
    <div className="flex h-16 items-center px-4">
      <Link
        href="/admin"
        className="flex min-w-0 items-center gap-3"
      >
        <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-sidebar-primary text-sidebar-primary-foreground">
          <span className="text-sm font-bold">P</span>
        </div>

        <span className="truncate text-lg font-semibold opacity-0 transition-opacity duration-150 group-hover:opacity-100">
          Phantom Force
        </span>
      </Link>
    </div>
  );
}
