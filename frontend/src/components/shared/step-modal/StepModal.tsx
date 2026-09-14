"use client";

import type { ReactNode } from "react";

import {
  BaseModal,
  type ModalSize,
} from "@/components/shared/modal";
import { Button } from "@/components/ui/button";

interface StepModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  steps: string[];
  currentStep: number;
  children: ReactNode;
  size?: ModalSize;
  backDisabled?: boolean;
  nextDisabled?: boolean;
  saveDisabled?: boolean;
  saveLoading?: boolean;
  nextLabel?: string;
  saveLabel?: string;
  closeLabel?: string;
  onBack: () => void;
  onNext: () => void;
  onSave: () => void;
}

export function StepModal({
  open,
  onOpenChange,
  title,
  description,
  steps,
  currentStep,
  children,
  size = "xl",
  backDisabled = false,
  nextDisabled = false,
  saveDisabled = false,
  saveLoading = false,
  nextLabel = "Next",
  saveLabel = "Save",
  closeLabel = "Close",
  onBack,
  onNext,
  onSave,
}: StepModalProps) {
  const isLastStep = currentStep >= steps.length - 1;

  return (
    <BaseModal
      open={open}
      onOpenChange={onOpenChange}
      title={title}
      description={description}
      size={size}
      preventClose={saveLoading}
      footer={
        <>
          <Button
            type="button"
            variant="outline"
            disabled={saveLoading}
            onClick={() => onOpenChange(false)}
          >
            {closeLabel}
          </Button>

          <Button
            type="button"
            variant="outline"
            disabled={
              backDisabled ||
              currentStep === 0 ||
              saveLoading
            }
            onClick={onBack}
          >
            Back
          </Button>

          <Button
            type="button"
            disabled={saveDisabled || saveLoading}
            onClick={isLastStep ? onSave : onNext}
          >
            {saveLoading
              ? "Saving..."
              : isLastStep
                ? saveLabel
                : nextLabel}
          </Button>
        </>
      }
    >
      <div className="space-y-5">
        <div className="grid gap-2 sm:grid-cols-2">
          {steps.map((step, index) => (
            <div
              key={step}
              className="flex items-center gap-2 rounded-lg border px-3 py-2 text-sm"
            >
              <span
                className="flex size-5 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-medium data-[current=true]:bg-primary data-[current=true]:text-primary-foreground"
                data-current={index === currentStep}
              >
                {index + 1}
              </span>
              <span className="truncate">{step}</span>
            </div>
          ))}
        </div>

        {children}
      </div>
    </BaseModal>
  );
}
