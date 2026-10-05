"use client";

import { LoaderCircle, PanelsTopLeft } from "lucide-react";

import { Button } from "@/components/ui/button";

interface MicrosoftLoginButtonProps {
  onClick: () => void;
  pending?: boolean;
  disabled?: boolean;
}

export function MicrosoftLoginButton({
  onClick,
  pending = false,
  disabled = false,
}: MicrosoftLoginButtonProps) {
  return (
    <Button
      type="button"
      variant="outline"
      size="lg"
      className="w-full"
      disabled={disabled || pending}
      onClick={onClick}
    >
      <LoaderCircle className={pending ? "animate-spin" : "hidden"} />
      <PanelsTopLeft className={pending ? "hidden" : undefined} />
      <span className={pending ? undefined : "hidden"}>Connecting...</span>
      <span className={pending ? "hidden" : undefined}>
        Continue with Microsoft
      </span>
    </Button>
  );
}
