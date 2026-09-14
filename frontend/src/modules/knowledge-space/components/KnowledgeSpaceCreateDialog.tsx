"use client";

import { useState } from "react";

import { FormModal } from "@/components/shared/modal";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useEnterpriseOptions } from "@/modules/enterprise";

import { useCreateKnowledgeSpace } from "../hooks";
import type { KnowledgeSpace } from "../types";

interface KnowledgeSpaceCreateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated?: (knowledgeSpace: KnowledgeSpace) => void;
}

const initialForm = {
  enterpriseId: "",
  name: "",
  code: "",
  description: "",
};

export function KnowledgeSpaceCreateDialog({
  open,
  onOpenChange,
  onCreated,
}: KnowledgeSpaceCreateDialogProps) {
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState<string | null>(null);
  const enterpriseOptionsQuery = useEnterpriseOptions();
  const createMutation = useCreateKnowledgeSpace();

  const canSubmit =
    form.enterpriseId.length > 0 &&
    form.name.trim().length > 0 &&
    form.code.trim().length > 0 &&
    !createMutation.isPending;

  async function handleSubmit() {
    if (!canSubmit) {
      return;
    }

    setError(null);

    try {
      const knowledgeSpace =
        await createMutation.mutateAsync({
          enterprise_id: form.enterpriseId,
          name: form.name.trim(),
          code: form.code.trim(),
          description:
            form.description.trim() || null,
          configuration: {},
        });

      setForm(initialForm);
      onOpenChange(false);
      onCreated?.(knowledgeSpace);
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Unable to create knowledge space.",
      );
    }
  }

  function handleOpenChange(nextOpen: boolean) {
    if (!nextOpen && !createMutation.isPending) {
      setError(null);
      setForm(initialForm);
    }

    onOpenChange(nextOpen);
  }

  return (
    <FormModal
      open={open}
      onOpenChange={handleOpenChange}
      title="New knowledge space"
      description="Create a workspace inside an enterprise."
      submitLabel="Create"
      submitLoading={createMutation.isPending}
      submitDisabled={!canSubmit}
      onSubmit={handleSubmit}
      size="lg"
    >
      <div className="grid gap-4">
        <div className="grid gap-2">
          <Label htmlFor="knowledge-space-enterprise">
            Enterprise
          </Label>
          <Select
            value={form.enterpriseId}
            onValueChange={(value) =>
              setForm((current) => ({
                ...current,
                enterpriseId: value ?? "",
              }))
            }
            disabled={enterpriseOptionsQuery.isLoading}
          >
            <SelectTrigger
              id="knowledge-space-enterprise"
              className="w-full"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {(enterpriseOptionsQuery.data ?? []).map(
                (enterprise) => (
                  <SelectItem
                    key={enterprise.id}
                    value={enterprise.id}
                  >
                    {enterprise.name}
                  </SelectItem>
                ),
              )}
            </SelectContent>
          </Select>
        </div>

        <div className="grid gap-2">
          <Label htmlFor="knowledge-space-name">
            Name
          </Label>
          <Input
            id="knowledge-space-name"
            value={form.name}
            maxLength={255}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                name: event.target.value,
              }))
            }
          />
        </div>

        <div className="grid gap-2">
          <Label htmlFor="knowledge-space-code">
            Code
          </Label>
          <Input
            id="knowledge-space-code"
            value={form.code}
            maxLength={100}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                code: event.target.value,
              }))
            }
          />
        </div>

        <div className="grid gap-2">
          <Label htmlFor="knowledge-space-description">
            Description
          </Label>
          <Textarea
            id="knowledge-space-description"
            value={form.description}
            rows={4}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                description: event.target.value,
              }))
            }
          />
        </div>

        {enterpriseOptionsQuery.isError && (
          <p className="text-sm text-destructive">
            Unable to load enterprises.
          </p>
        )}

        {error && (
          <p className="text-sm text-destructive">
            {error}
          </p>
        )}
      </div>
    </FormModal>
  );
}
