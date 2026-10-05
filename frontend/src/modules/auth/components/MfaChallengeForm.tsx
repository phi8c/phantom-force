"use client";

import { useState, type FormEvent } from "react";
import { KeyRound, LoaderCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface MfaChallengeFormProps {
  onSubmit: (code: string) => void;
  pending?: boolean;
  error?: string | null;
}

export function MfaChallengeForm({
  onSubmit,
  pending = false,
  error = null,
}: MfaChallengeFormProps) {
  const [code, setCode] = useState("");
  const canSubmit = code.length === 6 && !pending;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (canSubmit) {
      onSubmit(code);
    }
  }

  return (
    <form className="grid gap-4" onSubmit={handleSubmit}>
      <div className="grid gap-2">
        <Label htmlFor="auth-mfa-code">Authentication code</Label>
        <Input
          id="auth-mfa-code"
          name="one-time-code"
          type="text"
          inputMode="numeric"
          autoComplete="one-time-code"
          pattern="[0-9]{6}"
          maxLength={6}
          className="h-11 text-center font-mono text-lg"
          value={code}
          disabled={pending}
          required
          autoFocus
          onChange={(event) =>
            setCode(event.target.value.replace(/\D/g, "").slice(0, 6))
          }
        />
      </div>

      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}

      <Button
        type="submit"
        size="lg"
        className="w-full"
        disabled={!canSubmit}
      >
        <LoaderCircle className={pending ? "animate-spin" : "hidden"} />
        <KeyRound className={pending ? "hidden" : undefined} />
        <span className={pending ? undefined : "hidden"}>Verifying...</span>
        <span className={pending ? "hidden" : undefined}>Verify code</span>
      </Button>
    </form>
  );
}
