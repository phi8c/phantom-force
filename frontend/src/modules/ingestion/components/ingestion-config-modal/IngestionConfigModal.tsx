"use client";

import { useEffect, useMemo, useState } from "react";

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
  onOpenChange: (open: boolean) => void;
  onSaved?: () => void;
}

const steps = [
  "Processing",
  "Source Scope",
];

export function IngestionConfigModal({
  open,
  ingestionJobId,
  onOpenChange,
  onSaved,
}: IngestionConfigModalProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [extractionEngineCode, setExtractionEngineCode] =
    useState("");
  const [chunkingStrategyCode, setChunkingStrategyCode] =
    useState("");
  const [classification, setClassification] =
    useState(true);
  const [configurationText, setConfigurationText] =
    useState("{}");
  const [selectedRoots, setSelectedRoots] = useState<
    IngestionScopeRoot[]
  >([]);
  const [error, setError] = useState<string | null>(null);

  const extractionQuery = useExtractionEngines();
  const chunkingQuery = useChunkingStrategies();
  const configurationQuery =
    useIngestionConfiguration(ingestionJobId);
  const scopeQuery = useIngestionScope(ingestionJobId);

  const saveConfigurationMutation =
    useSaveIngestionConfiguration(ingestionJobId ?? "");
  const saveScopeMutation =
    useSaveIngestionScope(ingestionJobId ?? "");

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

    return selectedRoots.length === 0;
  }, [
    chunkingStrategyCode,
    currentStep,
    extractionEngineCode,
    ingestionJobId,
    loading,
    saving,
    selectedRoots.length,
  ]);

  useEffect(() => {
    if (!open) {
      return;
    }

    setCurrentStep(0);
    setError(null);
    setExtractionEngineCode("");
    setChunkingStrategyCode("");
    setClassification(true);
    setConfigurationText("{}");
    setSelectedRoots([]);
  }, [open, ingestionJobId]);

  useEffect(() => {
    if (!open || extractionEngineCode) {
      return;
    }

    const firstEngine = extractionQuery.data?.[0];
    if (firstEngine) {
      setExtractionEngineCode(firstEngine.code);
    }
  }, [extractionEngineCode, extractionQuery.data, open]);

  useEffect(() => {
    if (!open || chunkingStrategyCode) {
      return;
    }

    const firstStrategy = chunkingQuery.data?.[0];
    if (firstStrategy) {
      setChunkingStrategyCode(firstStrategy.code);
    }
  }, [chunkingQuery.data, chunkingStrategyCode, open]);

  useEffect(() => {
    const config = configurationQuery.data?.data;

    if (!open || !config) {
      return;
    }

    setClassification(config.is_classification);
    setConfigurationText(
      JSON.stringify(config.configuration ?? {}, null, 2),
    );
  }, [configurationQuery.data, open]);

  useEffect(() => {
    const scope = scopeQuery.data?.data?.scope_data;

    if (!open || !scope?.roots) {
      return;
    }

    setSelectedRoots(scope.roots);
  }, [open, scopeQuery.data]);

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
    if (!ingestionJobId) {
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
