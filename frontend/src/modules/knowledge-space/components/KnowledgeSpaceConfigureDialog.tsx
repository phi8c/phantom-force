"use client";

import { useEffect, useState } from "react";

import { StepModal } from "@/components/shared/step-modal";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useDataHubProviders } from "@/modules/data-hub-provider";
import { useEmbeddingModels } from "@/modules/embedding-model";

import {
  useKnowledgeSpaceDataHubConfig,
  useKnowledgeSpaceEmbeddingConfig,
  useSaveKnowledgeSpaceDataHubConfig,
  useSaveKnowledgeSpaceEmbeddingConfig,
} from "../hooks";
import type { KnowledgeSpaceListItem } from "../types";

interface KnowledgeSpaceConfigureDialogProps {
  open: boolean;
  knowledgeSpace: KnowledgeSpaceListItem | null;
  onOpenChange: (open: boolean) => void;
}

const steps = [
  "Data Hub",
  "Embedding Model",
];

export function KnowledgeSpaceConfigureDialog({
  open,
  knowledgeSpace,
  onOpenChange,
}: KnowledgeSpaceConfigureDialogProps) {
  const knowledgeSpaceId = knowledgeSpace?.id ?? null;
  const [currentStep, setCurrentStep] = useState(0);
  const [dataHubProviderId, setDataHubProviderId] =
    useState("");
  const [dataHubConfigText, setDataHubConfigText] =
    useState("{}");
  const [embeddingModelId, setEmbeddingModelId] =
    useState("");
  const [embeddingConfigText, setEmbeddingConfigText] =
    useState("{}");
  const [error, setError] = useState<string | null>(null);

  const providersQuery = useDataHubProviders();
  const embeddingModelsQuery = useEmbeddingModels();
  const dataHubConfigQuery =
    useKnowledgeSpaceDataHubConfig(knowledgeSpaceId);
  const embeddingConfigQuery =
    useKnowledgeSpaceEmbeddingConfig(knowledgeSpaceId);

  const saveDataHubMutation =
    useSaveKnowledgeSpaceDataHubConfig(
      knowledgeSpaceId ?? "",
    );
  const saveEmbeddingMutation =
    useSaveKnowledgeSpaceEmbeddingConfig(
      knowledgeSpaceId ?? "",
    );

  useEffect(() => {
    if (!open) {
      return;
    }

    setCurrentStep(0);
    setError(null);
    setDataHubProviderId("");
    setDataHubConfigText("{}");
    setEmbeddingModelId("");
    setEmbeddingConfigText("{}");
  }, [open, knowledgeSpaceId]);

  useEffect(() => {
    const config = dataHubConfigQuery.data?.data;

    if (!open || !config) {
      return;
    }

    setDataHubProviderId(config.data_hub_provider_id);
    setDataHubConfigText(
      JSON.stringify(config.configuration ?? {}, null, 2),
    );
  }, [dataHubConfigQuery.data, open]);

  useEffect(() => {
    const config = embeddingConfigQuery.data?.data;

    if (!open || !config) {
      return;
    }

    setEmbeddingModelId(config.embedding_model_id);
    setEmbeddingConfigText(
      JSON.stringify(config.configuration ?? {}, null, 2),
    );
  }, [embeddingConfigQuery.data, open]);

  const saving =
    saveDataHubMutation.isPending ||
    saveEmbeddingMutation.isPending;
  const loading =
    currentStep === 0
      ? providersQuery.isLoading ||
        dataHubConfigQuery.isLoading
      : embeddingModelsQuery.isLoading ||
        embeddingConfigQuery.isLoading;
  const saveDisabled =
    loading ||
    saving ||
    (currentStep === 0
      ? !dataHubProviderId
      : !embeddingModelId);

  async function handleSaveCurrentStep() {
    if (!knowledgeSpaceId) {
      return false;
    }

    setError(null);

    try {
      if (currentStep === 0) {
        await saveDataHubMutation.mutateAsync({
          data_hub_provider_id: dataHubProviderId,
          configuration: parseConfig(dataHubConfigText),
          enabled: true,
        });
      } else {
        await saveEmbeddingMutation.mutateAsync({
          embedding_model_id: embeddingModelId,
          configuration: parseConfig(embeddingConfigText),
          enabled: true,
        });
      }

      return true;
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Unable to save configuration.",
      );
      return false;
    }
  }

  async function handleNext() {
    const saved = await handleSaveCurrentStep();

    if (saved) {
      setCurrentStep(1);
    }
  }

  async function handleSave() {
    const saved = await handleSaveCurrentStep();

    if (saved) {
      onOpenChange(false);
    }
  }

  function handleOpenChange(nextOpen: boolean) {
    if (!nextOpen && saving) {
      return;
    }

    onOpenChange(nextOpen);
  }

  return (
    <StepModal
      open={open}
      onOpenChange={handleOpenChange}
      title="Configure knowledge space"
      description={knowledgeSpace?.name}
      steps={steps}
      currentStep={currentStep}
      saveDisabled={saveDisabled}
      saveLoading={saving}
      nextLabel="Save and next"
      saveLabel="Save"
      onBack={() => setCurrentStep(0)}
      onNext={handleNext}
      onSave={handleSave}
    >
      {currentStep === 0 ? (
        <DataHubStep
          providerId={dataHubProviderId}
          configText={dataHubConfigText}
          loading={loading}
          providers={providersQuery.data ?? []}
          onProviderChange={setDataHubProviderId}
          onConfigTextChange={setDataHubConfigText}
        />
      ) : (
        <EmbeddingStep
          embeddingModelId={embeddingModelId}
          configText={embeddingConfigText}
          loading={loading}
          embeddingModels={embeddingModelsQuery.data ?? []}
          onEmbeddingModelChange={setEmbeddingModelId}
          onConfigTextChange={setEmbeddingConfigText}
        />
      )}

      {error && (
        <p className="text-sm text-destructive">
          {error}
        </p>
      )}
    </StepModal>
  );
}

function DataHubStep({
  providerId,
  configText,
  loading,
  providers,
  onProviderChange,
  onConfigTextChange,
}: {
  providerId: string;
  configText: string;
  loading: boolean;
  providers: ReturnType<typeof useDataHubProviders>["data"];
  onProviderChange: (providerId: string) => void;
  onConfigTextChange: (configText: string) => void;
}) {
  return (
    <div className="grid gap-4">
      <div className="grid gap-2">
        <Label>Data Hub Provider</Label>
        <Select
          value={providerId}
          onValueChange={(value) =>
            onProviderChange(value ?? "")
          }
          disabled={loading}
        >
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {(providers ?? []).map((provider) => (
              <SelectItem
                key={provider.id}
                value={provider.id}
              >
                {provider.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid gap-2">
        <Label>Configuration</Label>
        <Textarea
          value={configText}
          rows={8}
          className="font-mono text-sm"
          onChange={(event) =>
            onConfigTextChange(event.target.value)
          }
        />
      </div>
    </div>
  );
}

function EmbeddingStep({
  embeddingModelId,
  configText,
  loading,
  embeddingModels,
  onEmbeddingModelChange,
  onConfigTextChange,
}: {
  embeddingModelId: string;
  configText: string;
  loading: boolean;
  embeddingModels: ReturnType<
    typeof useEmbeddingModels
  >["data"];
  onEmbeddingModelChange: (
    embeddingModelId: string,
  ) => void;
  onConfigTextChange: (configText: string) => void;
}) {
  return (
    <div className="grid gap-4">
      <div className="grid gap-2">
        <Label>Embedding Model</Label>
        <Select
          value={embeddingModelId}
          onValueChange={(value) =>
            onEmbeddingModelChange(value ?? "")
          }
          disabled={loading}
        >
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {(embeddingModels ?? []).map((model) => (
              <SelectItem key={model.id} value={model.id}>
                {model.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid gap-2">
        <Label>Configuration</Label>
        <Textarea
          value={configText}
          rows={8}
          className="font-mono text-sm"
          onChange={(event) =>
            onConfigTextChange(event.target.value)
          }
        />
      </div>
    </div>
  );
}

function parseConfig(
  text: string,
): Record<string, unknown> {
  try {
    const value = JSON.parse(text || "{}");

    if (
      value === null ||
      Array.isArray(value) ||
      typeof value !== "object"
    ) {
      throw new Error();
    }

    return value as Record<string, unknown>;
  } catch {
    throw new Error(
      "Configuration must be a valid JSON object.",
    );
  }
}
