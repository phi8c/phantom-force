"use client";

import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";

import {
  BaseModal,
  type ModalSize,
} from "./BaseModal";

interface FormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;

  title: string;
  description?: string;

  children: ReactNode;

  onSubmit: () => void;
  submitLabel?: string;
  cancelLabel?: string;

  submitDisabled?: boolean;
  submitLoading?: boolean;

  size?: ModalSize;

  closeOnOverlayClick?: boolean;
  closeOnEscape?: boolean;

  className?: string;
  contentClassName?: string;
}

export function FormModal({
  open,
  onOpenChange,
  title,
  description,
  children,
  onSubmit,
  submitLabel = "Save",
  cancelLabel = "Cancel",
  submitDisabled = false,
  submitLoading = false,
  size = "lg",
  closeOnOverlayClick = true,
  closeOnEscape = true,
  className,
  contentClassName,
}: FormModalProps) {
  const isSubmitting = submitLoading;

  return (
    <BaseModal
      open={open}
      onOpenChange={onOpenChange}
      title={title}
      description={description}
      size={size}
      closeOnOverlayClick={closeOnOverlayClick}
      closeOnEscape={closeOnEscape}
      preventClose={isSubmitting}
      className={className}
      contentClassName={contentClassName}
      footer={
        <>
          <Button
            type="button"
            variant="outline"
            disabled={isSubmitting}
            onClick={() => onOpenChange(false)}
          >
            {cancelLabel}
          </Button>

          <Button
            type="button"
            disabled={submitDisabled || isSubmitting}
            onClick={onSubmit}
          >
            {isSubmitting ? "Saving..." : submitLabel}
          </Button>
        </>
      }
    >
      {children}
    </BaseModal>
  );
}