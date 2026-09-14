"use client";

import type { DataTableColumn } from "@/components/shared/data-table";
import { DataTable } from "@/components/shared/data-table";

import type { Enterprise } from "../types";
import { EnterpriseStatusBadge } from "./EnterpriseStatusBadge";

interface EnterpriseTableProps {
  enterprises: Enterprise[];
  loading?: boolean;
}

const columns: DataTableColumn<Enterprise>[] = [
  {
    id: "code",
    header: "Code",
    accessorKey: "code",
    width: "180px",
    cellClassName: "font-medium",
  },
  {
    id: "name",
    header: "Name",
    accessorKey: "name",
  },
  {
    id: "description",
    header: "Description",
    cell: (enterprise) =>
      enterprise.description ? (
        <span className="line-clamp-1">
          {enterprise.description}
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
    cell: (enterprise) => (
      <EnterpriseStatusBadge status={enterprise.status} />
    ),
  },
  {
    id: "created",
    header: "Created",
    width: "180px",
    cell: (enterprise) =>
      enterprise.created_at
        ? new Intl.DateTimeFormat("en", {
            dateStyle: "medium",
            timeStyle: "short",
          }).format(new Date(enterprise.created_at))
        : "-",
  },
];

export function EnterpriseTable({
  enterprises,
  loading = false,
}: EnterpriseTableProps) {
  return (
    <DataTable
      columns={columns}
      data={enterprises}
      loading={loading}
      loadingMessage="Loading enterprises..."
      emptyMessage="No enterprises found."
      getRowId={(enterprise) => enterprise.id}
      className="rounded-none border-x-0"
    />
  );
}
