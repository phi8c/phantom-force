"use client";

import { Badge } from "@/components/ui/badge";

import type { Enterprise } from "../types";

interface EnterpriseStatusBadgeProps {
  status: Enterprise["status"];
}

export function EnterpriseStatusBadge({
  status,
}: EnterpriseStatusBadgeProps) {
  const isActive = status === "ACTIVE";

  return (
    <Badge variant={isActive ? "default" : "secondary"}>
      {isActive ? "Active" : "Inactive"}
    </Badge>
  );
}
