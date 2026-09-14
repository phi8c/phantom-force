"use client";

import type { ReactNode } from "react";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import { cn } from "@/lib/utils";

export type DataTableAlign = "left" | "center" | "right";

export interface DataTableColumn<TData> {
  id: string;
  header: ReactNode;
  accessorKey?: keyof TData;
  cell?: (row: TData, rowIndex: number) => ReactNode;

  headerClassName?: string;
  cellClassName?: string;

  align?: DataTableAlign;
  width?: string;
}

interface DataTableProps<TData> {
  columns: DataTableColumn<TData>[];
  data: TData[];

  getRowId?: (row: TData, rowIndex: number) => string;
  onRowClick?: (row: TData) => void;

  loading?: boolean;
  loadingMessage?: string;
  emptyMessage?: string;

  rowClassName?: string | ((row: TData, rowIndex: number) => string);
  className?: string;
}

export function DataTable<TData>({
  columns,
  data,
  getRowId,
  onRowClick,
  loading = false,
  loadingMessage = "Loading...",
  emptyMessage = "No data found.",
  rowClassName,
  className,
}: DataTableProps<TData>) {
  return (
    <div className={cn("rounded-xl border bg-card", className)}>
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            {columns.map((column) => (
              <TableHead
                key={column.id}
                style={{
                  width: column.width,
                }}
                className={cn(
                  getAlignClassName(column.align),
                  column.headerClassName,
                )}
              >
                {column.header}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>

        <TableBody>
          {loading ? (
            <TableRow>
              <TableCell
                colSpan={columns.length}
                className="h-32 text-center text-muted-foreground"
              >
                {loadingMessage}
              </TableCell>
            </TableRow>
          ) : data.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={columns.length}
                className="h-32 text-center text-muted-foreground"
              >
                {emptyMessage}
              </TableCell>
            </TableRow>
          ) : (
            data.map((row, rowIndex) => {
              const resolvedRowClassName =
                typeof rowClassName === "function"
                  ? rowClassName(row, rowIndex)
                  : rowClassName;

              return (
                <TableRow
                  key={
                    getRowId?.(row, rowIndex) ??
                    String(rowIndex)
                  }
                  className={cn(
                    onRowClick &&
                      "cursor-pointer",
                    resolvedRowClassName,
                  )}
                  onClick={() => onRowClick?.(row)}
                >
                  {columns.map((column) => (
                    <TableCell
                      key={column.id}
                      className={cn(
                        getAlignClassName(column.align),
                        column.cellClassName,
                      )}
                    >
                      {renderCell(column, row, rowIndex)}
                    </TableCell>
                  ))}
                </TableRow>
              );
            })
          )}
        </TableBody>
      </Table>
    </div>
  );
}

function renderCell<TData>(
  column: DataTableColumn<TData>,
  row: TData,
  rowIndex: number,
): ReactNode {
  if (column.cell) {
    return column.cell(row, rowIndex);
  }

  if (column.accessorKey) {
    const value = row[column.accessorKey];

    return value == null ? "-" : String(value);
  }

  return "-";
}

function getAlignClassName(
  align: DataTableAlign = "left",
): string {
  if (align === "center") {
    return "text-center";
  }

  if (align === "right") {
    return "text-right";
  }

  return "text-left";
}
