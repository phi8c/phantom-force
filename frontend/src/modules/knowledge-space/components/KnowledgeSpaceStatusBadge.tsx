"use client";

import { Badge } from "@/components/ui/badge";

import type { KnowledgeSpaceListItem } from "../types";

interface KnowledgeSpaceStatusBadgeProps {
  status: KnowledgeSpaceListItem["status"];
}

export function KnowledgeSpaceStatusBadge({
  status,
}: KnowledgeSpaceStatusBadgeProps) {
  const isActive = status === "ACTIVE";

  return (
    <Badge variant={isActive ? "default" : "secondary"}>
      {isActive ? "Active" : "Inactive"}
    </Badge>
  );
}
