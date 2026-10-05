"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { ErrorState } from "@/components/shared/error-state";

import { getAuthErrorMessage } from "../auth-errors";
import { useCurrentUser, useVerifyMfa } from "../hooks";
import { getSessionHomePath } from "../session-context";
import { AuthLoadingState } from "./AuthLoadingState";
import { MfaChallengeForm } from "./MfaChallengeForm";

export function AuthCallbackView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionQuery = useCurrentUser();
  const mfaMutation = useVerifyMfa();
  const [error, setError] = useState<string | null>(null);
  const status = searchParams.get("auth_status");
  const challengeId = searchParams.get("mfa_challenge_id");

  useEffect(() => {
    if (status === "success" && sessionQuery.data) {
      router.replace(getSessionHomePath(sessionQuery.data));
    }
  }, [router, sessionQuery.data, status]);

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

      if (result.status !== "success") {
        setError("Authentication could not be completed.");
        return;
      }

      const refreshedSession = await sessionQuery.refetch();
      if (refreshedSession.data) {
        router.replace(getSessionHomePath(refreshedSession.data));
      } else {
        setError("The authenticated session could not be loaded.");
      }
    } catch (caughtError) {
      setError(getAuthErrorMessage(caughtError, "The code could not be verified."));
    }
  }

  if (status === "mfa_required" && challengeId) {
    return (
      <main className="grid min-h-screen place-items-center bg-muted/30 p-4 sm:p-8">
        <div className="w-full max-w-sm rounded-lg border bg-card p-5">
          <h1 className="text-base font-semibold">Verify your identity</h1>
          <p className="mb-5 mt-1 text-sm text-muted-foreground">
            Enter the authentication code to complete sign in.
          </p>
          <MfaChallengeForm
            pending={mfaMutation.isPending}
            error={error}
            onSubmit={(code) => void handleMfa(code)}
          />
        </div>
      </main>
    );
  }

  if (status === "mfa_enrollment_required") {
    return (
      <ErrorState
        title="MFA enrollment required"
        description="This account must enroll in MFA before authentication can continue."
      />
    );
  }

  if (status !== "success") {
    return (
      <ErrorState
        title="Authentication was not completed"
        description="The callback result is missing or invalid. Start sign in again."
      />
    );
  }

  if (sessionQuery.isError) {
    return (
      <ErrorState
        title="Session could not be loaded"
        description={getAuthErrorMessage(
          sessionQuery.error,
          "Authentication completed, but the application session is unavailable.",
        )}
        onAction={() => void sessionQuery.refetch()}
      />
    );
  }

  return <AuthLoadingState />;
}
