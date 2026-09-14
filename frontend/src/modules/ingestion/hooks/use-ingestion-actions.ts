"use client";

import { useIngestionStore } from "../store/ingestion.store";

export function useIngestionActions() {
  const {
    openCreateDialog,
    closeCreateDialog,
    openDetailDialog,
    closeDetailDialog,
  } = useIngestionStore();

  return {
    openCreateDialog,
    closeCreateDialog,
    openDetailDialog,
    closeDetailDialog,
  };
}