"use client";

import type { ReactNode } from "react";

import { QueryProvider } from "./QueryProvider";
import { StoreProvider } from "@/store/provider";

interface AppProvidersProps {
  children: ReactNode;
}

export function AppProviders({ children }: AppProvidersProps) {
  return (
    <StoreProvider>
      <QueryProvider>{children}</QueryProvider>
    </StoreProvider>
  );
}