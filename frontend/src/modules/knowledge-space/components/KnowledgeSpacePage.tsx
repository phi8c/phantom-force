"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useEnterpriseOptions } from "@/modules/enterprise";

import {
  useKnowledgeSpaceList,
} from "../hooks";
import type {
  KnowledgeSpace,
  KnowledgeSpaceListItem,
  ListKnowledgeSpacesParams,
} from "../types";
import { KnowledgeSpaceControls } from "./KnowledgeSpaceControls";
import { KnowledgeSpaceConfigureDialog } from "./KnowledgeSpaceConfigureDialog";
import { KnowledgeSpaceCreateDialog } from "./KnowledgeSpaceCreateDialog";
import { KnowledgeSpaceTable } from "./KnowledgeSpaceTable";

const PAGE_SIZE = 20;

export function KnowledgeSpacePage() {
  const router = useRouter();
  const [createOpen, setCreateOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [enterpriseId, setEnterpriseId] = useState("all");
  const [search, setSearch] = useState("");
  const [configureTarget, setConfigureTarget] =
    useState<KnowledgeSpaceListItem | null>(null);

  const enterpriseOptionsQuery = useEnterpriseOptions();

  const listParams = useMemo<ListKnowledgeSpacesParams>(
    () => ({
      page,
      page_size: PAGE_SIZE,
      enterprise_id:
        enterpriseId === "all" ? null : enterpriseId,
      search: search.trim() || null,
    }),
    [enterpriseId, page, search],
  );

  const knowledgeSpacesQuery =
    useKnowledgeSpaceList(listParams);

  const total = knowledgeSpacesQuery.data?.total ?? 0;
  const totalPages = Math.max(
    1,
    Math.ceil(total / PAGE_SIZE),
  );
  const canGoPrevious = page > 1;
  const canGoNext = page < totalPages;

  function handleEnterpriseChange(nextEnterpriseId: string) {
    setEnterpriseId(nextEnterpriseId);
    setPage(1);
  }

  function handleSearchChange(nextSearch: string) {
    setSearch(nextSearch);
    setPage(1);
  }

  function handleOpen(
    knowledgeSpace: KnowledgeSpaceListItem,
  ) {
    router.push(
      `/admin/knowledge-spaces/${knowledgeSpace.id}`,
    );
  }

  function handleCreated(
    knowledgeSpace: KnowledgeSpace,
  ) {
    setPage(1);
    setConfigureTarget({
      id: knowledgeSpace.id,
      enterprise_id: knowledgeSpace.enterprise_id,
      enterprise_name: "",
      name: knowledgeSpace.name,
      code: knowledgeSpace.code,
      description: knowledgeSpace.description,
      status: knowledgeSpace.status,
      created_at: knowledgeSpace.created_at,
    });
  }

  function handleRefresh() {
    void knowledgeSpacesQuery.refetch();
    void enterpriseOptionsQuery.refetch();
  }

  return (
    <div className="flex min-h-full flex-col">
      <KnowledgeSpaceControls
        enterpriseId={enterpriseId}
        search={search}
        loading={knowledgeSpacesQuery.isFetching}
        enterpriseOptions={
          enterpriseOptionsQuery.data ?? []
        }
        enterpriseOptionsLoading={
          enterpriseOptionsQuery.isLoading
        }
        onEnterpriseChange={handleEnterpriseChange}
        onSearchChange={handleSearchChange}
        onCreate={() => setCreateOpen(true)}
        onRefresh={handleRefresh}
      />

      <div className="flex flex-col gap-3 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-sm font-semibold">
            Knowledge space list
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Page {page} of {totalPages} - {total} total
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={
              !canGoPrevious ||
              knowledgeSpacesQuery.isFetching
            }
            onClick={() => setPage((current) => current - 1)}
          >
            <ChevronLeft className="size-4" />
            Previous
          </Button>

          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={
              !canGoNext ||
              knowledgeSpacesQuery.isFetching
            }
            onClick={() => setPage((current) => current + 1)}
          >
            Next
            <ChevronRight className="size-4" />
          </Button>
        </div>
      </div>

      <KnowledgeSpaceTable
        knowledgeSpaces={
          knowledgeSpacesQuery.data?.items ?? []
        }
        loading={knowledgeSpacesQuery.isLoading}
        onOpen={handleOpen}
        onConfigure={setConfigureTarget}
      />

      {knowledgeSpacesQuery.isError && (
        <div className="px-6 py-3 text-sm text-destructive">
          Unable to load knowledge spaces.
        </div>
      )}

      <KnowledgeSpaceCreateDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        onCreated={handleCreated}
      />

      <KnowledgeSpaceConfigureDialog
        open={Boolean(configureTarget)}
        knowledgeSpace={configureTarget}
        onOpenChange={(open) => {
          if (!open) {
            setConfigureTarget(null);
          }
        }}
      />
    </div>
  );
}
