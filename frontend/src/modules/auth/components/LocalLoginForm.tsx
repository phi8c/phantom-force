"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { Eye, EyeOff, LoaderCircle, LogIn } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import type { LocalLoginPayload } from "../types";

interface LocalLoginFormProps {
  onSubmit: (credentials: LocalLoginPayload) => void;
  pending?: boolean;
  error?: string | null;
  submitLabel?: string;
  registerHref?: string;
}

export function LocalLoginForm({
  onSubmit,
  pending = false,
  error = null,
  submitLabel = "Sign in",
  registerHref,
}: LocalLoginFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const canSubmit =
    email.trim().length > 0 && password.length > 0 && !pending;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!canSubmit) {
      return;
    }

    onSubmit({
      email: email.trim(),
      password,
    });
  }

  return (
    <form className="grid gap-4" onSubmit={handleSubmit}>
      <div className="grid gap-2">
        <Label htmlFor="auth-email">Email</Label>
        <Input
          id="auth-email"
          name="email"
          type="email"
          autoComplete="email"
          maxLength={320}
          value={email}
          disabled={pending}
          required
          onChange={(event) => setEmail(event.target.value)}
        />
      </div>

      <div className="grid gap-2">
        <Label htmlFor="auth-password">Password</Label>
        <div className="relative">
          <Input
            id="auth-password"
            name="password"
            type={showPassword ? "text" : "password"}
            autoComplete="current-password"
            className="pr-10"
            value={password}
            disabled={pending}
            required
            onChange={(event) => setPassword(event.target.value)}
          />
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            className="absolute right-0.5 top-0.5"
            disabled={pending}
            aria-label={showPassword ? "Hide password" : "Show password"}
            aria-pressed={showPassword}
            onClick={() => setShowPassword((visible) => !visible)}
          >
            <EyeOff className={showPassword ? undefined : "hidden"} />
            <Eye className={showPassword ? "hidden" : undefined} />
          </Button>
        </div>
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
        <LogIn className={pending ? "hidden" : undefined} />
        <span className={pending ? undefined : "hidden"}>Signing in...</span>
        <span className={pending ? "hidden" : undefined}>{submitLabel}</span>
      </Button>

      {registerHref && (
        <p className="text-center text-sm text-muted-foreground">
          Need an account?{" "}
          <Link
            href={registerHref}
            className="font-medium text-foreground underline-offset-4 hover:underline"
          >
            Register
          </Link>
        </p>
      )}
    </form>
  );
}
