"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";

import { useEnterpriseList } from "../hooks";
import { EnterpriseControls } from "./EnterpriseControls";
import { EnterpriseCreateDialog } from "./EnterpriseCreateDialog";
import { EnterpriseTable } from "./EnterpriseTable";

const PAGE_SIZE = 20;

export function EnterprisePage() {
  const [createOpen, setCreateOpen] = useState(false);
  const [cursorStack, setCursorStack] = useState<
    (string | null)[]
  >([null]);
  const currentCursor =
    cursorStack[cursorStack.length - 1] ?? null;

  const enterprisesQuery = useEnterpriseList({
    cursor: currentCursor,
    limit: PAGE_SIZE,
  });

  const page = enterprisesQuery.data;
  const pageNumber = cursorStack.length;

  function handleNextPage() {
    if (!page?.next_cursor) {
      return;
    }

    setCursorStack((current) => [
      ...current,
      page.next_cursor,
    ]);
  }

  function handlePreviousPage() {
    setCursorStack((current) =>
      current.length > 1
        ? current.slice(0, -1)
        : current,
    );
  }

  function handleRefresh() {
    void enterprisesQuery.refetch();
  }

  return (
    <div className="flex min-h-full flex-col">
      <EnterpriseControls
        loading={enterprisesQuery.isFetching}
        onCreate={() => setCreateOpen(true)}
        onRefresh={handleRefresh}
      />

      <div className="flex items-center justify-between px-6 py-4">
        <div>
          <h2 className="text-sm font-semibold">
            Enterprise list
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Page {pageNumber}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={
              cursorStack.length <= 1 ||
              enterprisesQuery.isFetching
            }
            onClick={handlePreviousPage}
          >
            <ChevronLeft className="size-4" />
            Previous
          </Button>

          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={
              !page?.has_more ||
              !page.next_cursor ||
              enterprisesQuery.isFetching
            }
            onClick={handleNextPage}
          >
            Next
            <ChevronRight className="size-4" />
          </Button>
        </div>
      </div>

      <EnterpriseTable
        enterprises={page?.items ?? []}
        loading={enterprisesQuery.isLoading}
      />

      {enterprisesQuery.isError && (
        <div className="px-6 py-3 text-sm text-destructive">
          Unable to load enterprises.
        </div>
      )}

      <EnterpriseCreateDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
      />
    </div>
  );
}
