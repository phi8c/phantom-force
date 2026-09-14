"use client";

import { create } from "zustand";

interface IngestionStore {
  selectedJobId: string | null;
  isCreateDialogOpen: boolean;
  isDetailDialogOpen: boolean;

  openCreateDialog: () => void;
  closeCreateDialog: () => void;

  openDetailDialog: (jobId: string) => void;
  closeDetailDialog: () => void;
}

export const useIngestionStore = create<IngestionStore>((set) => ({
  selectedJobId: null,
  isCreateDialogOpen: false,
  isDetailDialogOpen: false,

  openCreateDialog: () =>
    set({
      isCreateDialogOpen: true,
    }),

  closeCreateDialog: () =>
    set({
      isCreateDialogOpen: false,
    }),

  openDetailDialog: (jobId) =>
    set({
      selectedJobId: jobId,
      isDetailDialogOpen: true,
    }),

  closeDetailDialog: () =>
    set({
      selectedJobId: null,
      isDetailDialogOpen: false,
    }),
}));