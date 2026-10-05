import type { ReactNode } from "react";

import { ManagementAuthBoundary } from "@/modules/auth";

interface AdminLayoutProps {
  children: ReactNode;
}

export default function AdminLayout({
  children,
}: AdminLayoutProps) {
  return (
    <ManagementAuthBoundary>
      {children}
    </ManagementAuthBoundary>
  );
}
