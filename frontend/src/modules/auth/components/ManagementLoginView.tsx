"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

import { getAuthErrorMessage } from "../auth-errors";
import {
  useManagementLogin,
  useStartManagementOidc,
  useVerifyMfa,
} from "../hooks";
import type { LocalLoginPayload } from "../types";
import { LocalLoginForm } from "./LocalLoginForm";
import { MfaChallengeForm } from "./MfaChallengeForm";
import { MicrosoftLoginButton } from "./MicrosoftLoginButton";

export function ManagementLoginView() {
  const router = useRouter();
  const loginMutation = useManagementLogin();
  const oidcMutation = useStartManagementOidc();
  const mfaMutation = useVerifyMfa();
  const [challengeId, setChallengeId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleLocalLogin(credentials: LocalLoginPayload) {
    setError(null);

    try {
      const result = await loginMutation.mutateAsync(credentials);

      if (result.status === "success") {
        router.replace("/admin");
        return;
      }

      if (result.status === "mfa_required" && result.mfa_challenge_id) {
        setChallengeId(result.mfa_challenge_id);
        return;
      }

      setError("MFA enrollment is required before this account can sign in.");
    } catch (caughtError) {
      setError(getAuthErrorMessage(caughtError, "Sign in failed."));
    }
  }

  async function handleMfa(code: string) {
    if (!challengeId) {
      return;
    }

    setError(null);

    try {
      const result = await mfaMutation.mutateAsync({
        challenge_id: challengeId,
        code,
      });

      if (result.status === "success") {
        router.replace("/admin");
      }
    } catch (caughtError) {
      setError(getAuthErrorMessage(caughtError, "The code could not be verified."));
    }
  }

  async function handleMicrosoftLogin() {
    setError(null);

    try {
      const result = await oidcMutation.mutateAsync();
      window.location.assign(result.authorization_url);
    } catch (caughtError) {
      setError(
        getAuthErrorMessage(caughtError, "Microsoft sign in could not be started."),
      );
    }
  }

  const pending =
    loginMutation.isPending ||
    oidcMutation.isPending ||
    mfaMutation.isPending;

  return (
    <main className="grid min-h-screen place-items-center bg-muted/30 p-4 sm:p-8">
      <Card className="w-full max-w-md rounded-lg">
        <CardHeader className="gap-3 border-b">
          <div className="grid size-10 place-items-center rounded-lg bg-primary text-primary-foreground">
            <ShieldCheck className="size-5" />
          </div>
          <div>
            <CardTitle>Management sign in</CardTitle>
            <CardDescription className="mt-1">
              Access the Phantom Force administration workspace.
            </CardDescription>
          </div>
        </CardHeader>

        <CardContent className="grid gap-5">
          {challengeId ? (
            <MfaChallengeForm
              pending={mfaMutation.isPending}
              error={error}
              onSubmit={(code) => void handleMfa(code)}
            />
          ) : (
            <>
              <LocalLoginForm
                pending={pending}
                error={error}
                registerHref="/register"
                onSubmit={(credentials) => void handleLocalLogin(credentials)}
              />

              <div className="flex items-center gap-3">
                <Separator className="flex-1" />
                <span className="text-xs text-muted-foreground">or</span>
                <Separator className="flex-1" />
              </div>

              <MicrosoftLoginButton
                pending={oidcMutation.isPending}
                disabled={pending}
                onClick={() => void handleMicrosoftLogin()}
              />
            </>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
