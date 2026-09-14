"use client";

import { useMemo } from "react";

import { IngestionControls } from "./IngestionControls";
import { IngestionCreateDialog } from "./IngestionCreateDialog";
import { IngestionDetailDialog } from "./IngestionDetailDialog";
import { IngestionJobsTable } from "./IngestionJobsTable";
import { IngestionTabs } from "./IngestionTabs";

import { useIngestionFilters } from "../hooks/use-ingestion-filters";
import { useIngestionJobs } from "../hooks/use-ingestion-jobs";
import { useIngestionStore } from "../store/ingestion.store";


interface IngestionPageProps {
  knowledgeSpaceId?: string;
}

export function IngestionPage({knowledgeSpaceId}: IngestionPageProps) {
  const {
    filters,
    updateFilters,
    resetFilters,
  } = useIngestionFilters();

  const jobs = useIngestionJobs(filters);

  const {
    selectedJobId,
    isCreateDialogOpen,
    isDetailDialogOpen,
    openCreateDialog,
    closeCreateDialog,
    openDetailDialog,
    closeDetailDialog,
  } = useIngestionStore();

  const selectedJob = useMemo(
    () =>
      jobs.find((job) => job.id === selectedJobId),
    [jobs, selectedJobId],
  );

  function handleRefresh() {
    resetFilters();
  }

  return (
    <div className="flex min-h-full flex-col">
      

      <IngestionTabs />

      <IngestionControls
        filters={filters}
        onFilterChange={updateFilters}
        onReset={resetFilters}
        onRefresh={handleRefresh}
        onCreate={openCreateDialog}
      />

      <div className="flex items-center justify-between px-6 py-4 h-8">
        <div>
          <h2 className="text-sm font-semibold">
            Ingestion jobs
          </h2>

         
        </div>
      </div>

      <IngestionJobsTable
        jobs={jobs}
        onRowClick={(job) => openDetailDialog(job.id)}
      />

      <IngestionCreateDialog
        open={isCreateDialogOpen}
        onClose={closeCreateDialog}
      />

      <IngestionDetailDialog
        job={selectedJob}
        open={isDetailDialogOpen}
        onClose={closeDetailDialog}
      />
    </div>
  );
}