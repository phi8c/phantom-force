"use client";

import { useState } from "react";

import type { IngestionFilters } from "../types/ingestion.types";

const initialFilters: IngestionFilters = {
  search: "",
  status: "ALL",
  source: "ALL",
};

export function useIngestionFilters() {
  const [filters, setFilters] =
    useState<IngestionFilters>(initialFilters);

  function updateFilters(
    values: Partial<IngestionFilters>,
  ) {
    setFilters((current) => ({
      ...current,
      ...values,
    }));
  }

  function resetFilters() {
    setFilters(initialFilters);
  }

  return {
    filters,
    updateFilters,
    resetFilters,
  };
}