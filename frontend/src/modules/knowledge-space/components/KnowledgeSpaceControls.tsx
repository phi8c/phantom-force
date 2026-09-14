"use client";

import { Plus, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import type { EnterpriseOption } from "@/modules/enterprise";

interface KnowledgeSpaceControlsProps {
  enterpriseId: string;
  search: string;
  loading?: boolean;
  enterpriseOptions: EnterpriseOption[];
  enterpriseOptionsLoading?: boolean;
  onEnterpriseChange: (enterpriseId: string) => void;
  onSearchChange: (search: string) => void;
  onCreate: () => void;
  onRefresh: () => void;
}

export function KnowledgeSpaceControls({
  enterpriseId,
  search,
  loading = false,
  enterpriseOptions,
  enterpriseOptionsLoading = false,
  onEnterpriseChange,
  onSearchChange,
  onCreate,
  onRefresh,
}: KnowledgeSpaceControlsProps) {
  return (
    <div className="border-b px-6 py-3">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">
            Knowledge Spaces
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage spaces across enterprises.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="icon"
            disabled={loading}
            onClick={onRefresh}
            aria-label="Refresh knowledge spaces"
            title="Refresh"
          >
            <RefreshCw className="size-4" />
          </Button>

          <Button type="button" onClick={onCreate}>
            <Plus className="size-4" />
            New knowledge space
          </Button>
        </div>
      </div>

      <div className="mt-3 grid gap-2 md:grid-cols-[minmax(220px,320px)_minmax(240px,1fr)]">
        <Select
          value={enterpriseId}
          onValueChange={(value) =>
            onEnterpriseChange(value ?? "all")
          }
          disabled={enterpriseOptionsLoading}
        >
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">
              All enterprises
            </SelectItem>
            {enterpriseOptions.map((enterprise) => (
              <SelectItem
                key={enterprise.id}
                value={enterprise.id}
              >
                {enterprise.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Input
          value={search}
          onChange={(event) =>
            onSearchChange(event.target.value)
          }
          placeholder="Search name or code"
        />
      </div>
    </div>
  );
}
