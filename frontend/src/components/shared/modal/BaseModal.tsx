"use client";

import type { ReactNode } from "react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import { cn } from "@/lib/utils";

export type ModalSize =
  | "sm"
  | "md"
  | "lg"
  | "xl"
  | "2xl"
  | "full";

interface BaseModalProps {
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

export function BaseModal({
  open,
  onOpenChange,
  title,
  description,
  children,
  footer,
  size = "md",
  closeOnOverlayClick = true,
  closeOnEscape = true,
  showCloseButton = true,
  preventClose = false,
  className,
  contentClassName,
  footerClassName,
}: BaseModalProps) {
  function handleOpenChange(nextOpen: boolean) {
    if (preventClose && !nextOpen) {
      return;
    }

    onOpenChange(nextOpen);
  }

  return (
    <Dialog
      open={open}
      onOpenChange={handleOpenChange}
    >
      <DialogContent
        showCloseButton={showCloseButton && !preventClose}
        className={cn(
          getModalSizeClassName(size),
          className,
        )}
      >
        {(title || description) && (
          <DialogHeader>
            {title && (
              <DialogTitle>
                {title}
              </DialogTitle>
            )}

            {description && (
              <DialogDescription>
                {description}
              </DialogDescription>
            )}
          </DialogHeader>
        )}

        <div
          className={cn(
            "min-w-0",
            contentClassName,
          )}
        >
          {children}
        </div>

        {footer && (
          <DialogFooter className={footerClassName}>
            {footer}
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  );
}

function getModalSizeClassName(
  size: ModalSize,
): string {
  switch (size) {
    case "sm":
      return "sm:max-w-sm";

    case "md":
      return "sm:max-w-md";

    case "lg":
      return "sm:max-w-lg";

    case "xl":
      return "sm:max-w-xl";

    case "2xl":
      return "sm:max-w-2xl";

    case "full":
      return "h-[calc(100vh-2rem)] w-[calc(100vw-2rem)] max-w-none";

    default:
      return "sm:max-w-md";
  }
}