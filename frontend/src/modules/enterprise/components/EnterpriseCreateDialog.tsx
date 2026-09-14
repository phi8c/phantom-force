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

import { useCreateEnterprise } from "../hooks";
import type { EnterpriseStatus } from "../types";

interface EnterpriseCreateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const initialForm = {
  code: "",
  name: "",
  description: "",
  status: "ACTIVE" as EnterpriseStatus,
};

export function EnterpriseCreateDialog({
  open,
  onOpenChange,
}: EnterpriseCreateDialogProps) {
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState<string | null>(null);
  const createMutation = useCreateEnterprise();

  const canSubmit =
    form.code.trim().length > 0 &&
    form.name.trim().length > 0 &&
    !createMutation.isPending;

  async function handleSubmit() {
    if (!canSubmit) {
      return;
    }

    setError(null);

    try {
      await createMutation.mutateAsync({
        code: form.code.trim(),
        name: form.name.trim(),
        description:
          form.description.trim() || null,
        status: form.status,
      });

      setForm(initialForm);
      onOpenChange(false);
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Unable to create enterprise.",
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
      title="New enterprise"
      description="Create an organization for top-level administration."
      submitLabel="Create"
      submitLoading={createMutation.isPending}
      submitDisabled={!canSubmit}
      onSubmit={handleSubmit}
      size="lg"
    >
      <div className="grid gap-4">
        <div className="grid gap-2">
          <Label htmlFor="enterprise-code">
            Code
          </Label>
          <Input
            id="enterprise-code"
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
          <Label htmlFor="enterprise-name">
            Name
          </Label>
          <Input
            id="enterprise-name"
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
          <Label htmlFor="enterprise-status">
            Status
          </Label>
          <Select
            value={form.status}
            onValueChange={(value) =>
              setForm((current) => ({
                ...current,
                status: value as EnterpriseStatus,
              }))
            }
          >
            <SelectTrigger
              id="enterprise-status"
              className="w-full"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ACTIVE">
                Active
              </SelectItem>
              <SelectItem value="INACTIVE">
                Inactive
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="grid gap-2">
          <Label htmlFor="enterprise-description">
            Description
          </Label>
          <Textarea
            id="enterprise-description"
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

        {error && (
          <p className="text-sm text-destructive">
            {error}
          </p>
        )}
      </div>
    </FormModal>
  );
}
