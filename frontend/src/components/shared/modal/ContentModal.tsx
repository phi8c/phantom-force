"use client";

import type { ReactNode } from "react";

import { BaseModal, type ModalSize } from "./BaseModal";

interface ContentModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;

  title?: string;
  description?: string;

  children: ReactNode;
  footer?: ReactNode;

  size?: ModalSize;

  closeOnOverlayClick?: boolean;
  closeOnEscape?: boolean;
  showCloseButton?: boolean;
  preventClose?: boolean;

  className?: string;
  contentClassName?: string;
  footerClassName?: string;
}

export function ContentModal({
  open,
  onOpenChange,
  title,
  description,
  children,
  footer,
  size = "lg",
  closeOnOverlayClick = true,
  closeOnEscape = true,
  showCloseButton = true,
  preventClose = false,
  className,
  contentClassName,
  footerClassName,
}: ContentModalProps) {
  return (
    <BaseModal
      open={open}
      onOpenChange={onOpenChange}
      title={title}
      description={description}
      size={size}
      closeOnOverlayClick={closeOnOverlayClick}
      closeOnEscape={closeOnEscape}
      showCloseButton={showCloseButton}
      preventClose={preventClose}
      className={className}
      contentClassName={contentClassName}
      footer={footer}
      footerClassName={footerClassName}
    >
      {children}
    </BaseModal>
  );
}