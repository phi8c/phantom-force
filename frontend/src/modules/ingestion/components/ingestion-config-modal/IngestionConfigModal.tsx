"use client";

import { useMemo, useState } from "react";

import { StepModal } from "@/components/shared/step-modal";

import {
  useChunkingStrategies,
  useExtractionEngines,
  useIngestionConfiguration,
  useIngestionScope,
  useSaveIngestionConfiguration,
  useSaveIngestionScope,
} from "../../hooks/use-ingestion-config";
import type { IngestionScopeRoot } from "../../types/ingestion.types";
import { ProcessingStep } from "./processing-step";
import { SourceScopeStep } from "./source-scope-step";

interface IngestionConfigModalProps {
  open: boolean;
  ingestionJobId: string | null;
  knowledgeSpaceId?: string;
  onOpenChange: (open: boolean) => void;
  onSaved?: () => void;
}

const steps = [
  "Processing",
  "Source Scope",
];

export function IngestionConfigModal(props: IngestionConfigModalProps) {
  if (!props.open || !props.ingestionJobId) return null;
  return <IngestionConfigForm key={props.ingestionJobId} {...props} />;
}

function IngestionConfigForm({
  open,
  ingestionJobId,
  knowledgeSpaceId,
  onOpenChange,
  onSaved,
}: IngestionConfigModalProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [extractionEngineOverride, setExtractionEngineCode] = useState<string | null>(null);
  const [chunkingStrategyOverride, setChunkingStrategyCode] = useState<string | null>(null);
  const [classificationOverride, setClassification] = useState<boolean | null>(null);
  const [configurationOverride, setConfigurationText] = useState<string | null>(null);
  const [rootsOverride, setSelectedRoots] = useState<IngestionScopeRoot[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const extractionQuery = useExtractionEngines(open);
  const chunkingQuery = useChunkingStrategies(open);
  const configurationQuery =
    useIngestionConfiguration(ingestionJobId, open);
  const scopeQuery = useIngestionScope(ingestionJobId, open);

  const saveConfigurationMutation =
    useSaveIngestionConfiguration(ingestionJobId ?? "");
  const saveScopeMutation =
    useSaveIngestionScope(ingestionJobId ?? "");

  // Server values remain the defaults until the user edits a field. The keyed
  // form remounts on close/job change, so no effects or extra renders reset state.
  const config = configurationQuery.data?.data;
  const extractionEngineCode = extractionEngineOverride ??
    extractionQuery.data?.find((item) => item.id === config?.extraction_engine_id)?.code ??
    extractionQuery.data?.[0]?.code ?? '';
  const chunkingStrategyCode = chunkingStrategyOverride ??
    chunkingQuery.data?.find((item) => item.id === config?.chunking_strategy_id)?.code ??
    chunkingQuery.data?.[0]?.code ?? '';
  const classification = classificationOverride ?? config?.is_classification ?? true;
  const configurationText = configurationOverride ?? JSON.stringify(config?.configuration ?? {}, null, 2);
  const selectedRoots = rootsOverride ?? scopeQuery.data?.data?.scope_data?.roots ?? [];

  const loading =
    extractionQuery.isLoading ||
    chunkingQuery.isLoading ||
    configurationQuery.isLoading ||
    scopeQuery.isLoading;
  const saving =
    saveConfigurationMutation.isPending ||
    saveScopeMutation.isPending;

  const saveDisabled = useMemo(() => {
    if (loading || saving || !ingestionJobId) {
      return true;
    }

    if (currentStep === 0) {
      return !extractionEngineCode || !chunkingStrategyCode;
    }

    return !knowledgeSpaceId || selectedRoots.length === 0;
  }, [
    chunkingStrategyCode,
    currentStep,
    extractionEngineCode,
    ingestionJobId,
    knowledgeSpaceId,
    loading,
    saving,
    selectedRoots.length,
  ]);

  async function handleSaveProcessing() {
    if (!ingestionJobId) {
      return false;
    }

    setError(null);

    try {
      await saveConfigurationMutation.mutateAsync({
        extraction_engine_code: extractionEngineCode,
        chunking_strategy_code: chunkingStrategyCode,
        model_set_code: null,
        is_classification: classification,
        configuration: parseJsonObject(configurationText),
      });

      return true;
    } catch (caughtError) {
      setError(toErrorMessage(caughtError));
      return false;
    }
  }

  async function handleNext() {
    const saved = await handleSaveProcessing();

    if (saved) {
      setCurrentStep(1);
    }
  }

  async function handleSaveScope() {
    if (!ingestionJobId || !knowledgeSpaceId) {
      return;
    }

    setError(null);

    try {
      await saveScopeMutation.mutateAsync({
        scope_type: "SELECTED_ROOTS",
        scope_data: {
          roots: selectedRoots,
        },
      });

      onSaved?.();
      onOpenChange(false);
    } catch (caughtError) {
      setError(toErrorMessage(caughtError));
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
      title="Configure ingestion"
      description={ingestionJobId ?? undefined}
      steps={steps}
      currentStep={currentStep}
      saveDisabled={saveDisabled}
      saveLoading={saving}
      nextLabel="Save and next"
      saveLabel="Done"
      closeLabel="Close"
      size="2xl"
      onBack={() => setCurrentStep(0)}
      onNext={handleNext}
      onSave={handleSaveScope}
    >
      {currentStep === 0 ? (
        <ProcessingStep
          extractionEngineCode={extractionEngineCode}
          chunkingStrategyCode={chunkingStrategyCode}
          classification={classification}
          configurationText={configurationText}
          loading={loading}
          extractionEngines={extractionQuery.data ?? []}
          chunkingStrategies={chunkingQuery.data ?? []}
          onExtractionEngineChange={setExtractionEngineCode}
          onChunkingStrategyChange={setChunkingStrategyCode}
          onClassificationChange={setClassification}
          onConfigurationTextChange={setConfigurationText}
        />
      ) : (
        <SourceScopeStep
          knowledgeSpaceId={knowledgeSpaceId}
          selectedRoots={selectedRoots}
          onSelectedRootsChange={setSelectedRoots}
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

function parseJsonObject(
  value: string,
): Record<string, unknown> {
  try {
    const parsed = JSON.parse(value || "{}");

    if (
      parsed === null ||
      Array.isArray(parsed) ||
      typeof parsed !== "object"
    ) {
      throw new Error();
    }

    return parsed as Record<string, unknown>;
  } catch {
    throw new Error(
      "Configuration must be a valid JSON object.",
    );
  }
}

function toErrorMessage(error: unknown) {
  return error instanceof Error
    ? error.message
    : "Unable to save ingestion configuration.";
}
