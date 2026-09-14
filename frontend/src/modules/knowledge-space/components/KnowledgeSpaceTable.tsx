"use client";

import { MoreHorizontal, Settings } from "lucide-react";

import type { DataTableColumn } from "@/components/shared/data-table";
import { DataTable } from "@/components/shared/data-table";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import type { KnowledgeSpaceListItem } from "../types";
import { KnowledgeSpaceStatusBadge } from "./KnowledgeSpaceStatusBadge";

interface KnowledgeSpaceTableProps {
  knowledgeSpaces: KnowledgeSpaceListItem[];
  loading?: boolean;
  onOpen: (knowledgeSpace: KnowledgeSpaceListItem) => void;
  onConfigure: (knowledgeSpace: KnowledgeSpaceListItem) => void;
}

const dateFormatter = new Intl.DateTimeFormat("en", {
  dateStyle: "medium",
  timeStyle: "short",
});

export function KnowledgeSpaceTable({
  knowledgeSpaces,
  loading = false,
  onOpen,
  onConfigure,
}: KnowledgeSpaceTableProps) {
  const columns: DataTableColumn<KnowledgeSpaceListItem>[] = [
    {
      id: "name",
      header: "Name",
      width: "260px",
      cellClassName: "font-medium",
      cell: (knowledgeSpace) => (
        <div className="min-w-0">
          <p className="truncate font-medium">
            {knowledgeSpace.name}
          </p>
          <p className="mt-1 truncate font-mono text-xs text-muted-foreground">
            {knowledgeSpace.code}
          </p>
        </div>
      ),
    },
    {
      id: "enterprise",
      header: "Enterprise",
      accessorKey: "enterprise_name",
      width: "220px",
    },
    {
      id: "description",
      header: "Description",
      cell: (knowledgeSpace) =>
        knowledgeSpace.description ? (
          <span className="line-clamp-1">
            {knowledgeSpace.description}
          </span>
        ) : (
          <span className="text-muted-foreground">
            No description
          </span>
        ),
    },
    {
      id: "status",
      header: "Status",
      width: "120px",
      cell: (knowledgeSpace) => (
        <KnowledgeSpaceStatusBadge
          status={knowledgeSpace.status}
        />
      ),
    },
    {
      id: "created",
      header: "Created",
      width: "180px",
      cell: (knowledgeSpace) =>
        knowledgeSpace.created_at
          ? dateFormatter.format(
              new Date(knowledgeSpace.created_at),
            )
          : "-",
    },
    {
      id: "actions",
      header: "",
      align: "right",
      width: "120px",
      cell: (knowledgeSpace) => (
        <div
          className="flex justify-end"
          onClick={(event) => event.stopPropagation()}
        >
          <DropdownMenu>
            <DropdownMenuTrigger
              render={
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  aria-label="Knowledge space actions"
                  title="Actions"
                >
                  <MoreHorizontal className="size-4" />
                </Button>
              }
            />
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={() => onOpen(knowledgeSpace)}
              >
                Open
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() =>
                  onConfigure(knowledgeSpace)
                }
              >
                <Settings className="size-4" />
                Configure
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={knowledgeSpaces}
      loading={loading}
      loadingMessage="Loading knowledge spaces..."
      emptyMessage="No knowledge spaces found."
      getRowId={(knowledgeSpace) => knowledgeSpace.id}
      onRowClick={onOpen}
      className="rounded-none border-x-0"
    />
  );
}
