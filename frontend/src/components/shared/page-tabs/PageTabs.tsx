"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { cn } from "@/lib/utils";

export interface PageTabItem {
  value: string;
  label: string;
  disabled?: boolean;
}

interface PageTabsProps {
  tabs: PageTabItem[];
  queryKey?: string;
  defaultValue?: string;
  className?: string;
}

export function PageTabs({
  tabs,
  queryKey = "tab",
  defaultValue,
  className,
}: PageTabsProps) {
  const searchParams = useSearchParams();

  const activeValue =
    searchParams.get(queryKey) ??
    defaultValue ??
    tabs[0]?.value;

  return (
    <div
      className={cn(
        "border-b",
        className,
      )}
    >
      <div className="flex items-center gap-6 overflow-x-auto px-6">
        {tabs.map((tab) => {
          const isActive = tab.value === activeValue;

          const params = new URLSearchParams(
            searchParams.toString(),
          );

          params.set(queryKey, tab.value);

          return (
            <Link
              key={tab.value}
              href={`?${params.toString()}`}
              aria-current={isActive ? "page" : undefined}
              aria-disabled={tab.disabled}
              tabIndex={tab.disabled ? -1 : undefined}
              className={cn(
                "relative flex h-11 shrink-0 items-center border-b-2 px-1 text-sm font-medium transition-colors",
                "text-muted-foreground hover:text-foreground",
                isActive &&
                  "border-primary text-foreground",
                !isActive && "border-transparent",
                tab.disabled &&
                  "pointer-events-none opacity-50",
              )}
            >
              {tab.label}
            </Link>
          );
        })}
      </div>
    </div>
  );
}