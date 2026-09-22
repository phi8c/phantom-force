import Link from "next/link";
import { ChevronRight, type LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

interface AdminSidebarNavigationItemProps {
  title: string;
  href: string;
  icon: LucideIcon;
  active: boolean;
}

export function AdminSidebarNavigationItem({
  title,
  href,
  icon: Icon,
  active,
}: AdminSidebarNavigationItemProps) {
  return (
    <Link
      href={href}
      title={title}
      className={cn(
        "group/item flex h-10 items-center gap-3 rounded-lg px-3 text-sm font-medium transition-colors",
        active
          ? "bg-sidebar-accent text-sidebar-accent-foreground"
          : "text-sidebar-foreground hover:bg-sidebar-accent/40 hover:text-sidebar-accent-foreground",
      )}
    >
      <Icon className="size-4 shrink-0" />

      <span className="min-w-0 flex-1 truncate whitespace-nowrap opacity-0 transition-opacity duration-150 group-hover:opacity-100">
        {title}
      </span>

      <ChevronRight
        className={cn(
          "size-3.5 shrink-0 opacity-0 transition-opacity duration-150",
          "group-hover:opacity-60",
          active && "opacity-60",
        )}
      />
    </Link>
  );
}
