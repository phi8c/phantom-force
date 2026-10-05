"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Database } from "lucide-react";

import { ErrorState } from "@/components/shared/error-state";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

import { getAuthErrorMessage } from "../auth-errors";
import {
  useKnowledgeSpaceAuthRequirement,
  useKnowledgeSpaceLogin,
  useStartKnowledgeSpaceOidc,
  useVerifyMfa,
} from "../hooks";
import type { LocalLoginPayload } from "../types";
import { LocalLoginForm } from "./LocalLoginForm";
import { MfaChallengeForm } from "./MfaChallengeForm";
import { MicrosoftLoginButton } from "./MicrosoftLoginButton";

interface KnowledgeSpaceLoginViewProps {
  knowledgeSpaceId: string;
}

export function KnowledgeSpaceLoginView({
  knowledgeSpaceId,
}: KnowledgeSpaceLoginViewProps) {
  const router = useRouter();
  const requirementQuery = useKnowledgeSpaceAuthRequirement(knowledgeSpaceId);
  const loginMutation = useKnowledgeSpaceLogin(knowledgeSpaceId);
  const oidcMutation = useStartKnowledgeSpaceOidc(knowledgeSpaceId);
  const mfaMutation = useVerifyMfa();
  const [challengeId, setChallengeId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const chatPath = `/chat/${encodeURIComponent(knowledgeSpaceId)}`;

  async function handleLocalLogin(credentials: LocalLoginPayload) {
    setError(null);

    try {
      const result = await loginMutation.mutateAsync(credentials);

      if (result.status === "success") {
        router.replace(chatPath);
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
        router.replace(chatPath);
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

  if (requirementQuery.isLoading) {
    return <KnowledgeSpaceLoginSkeleton />;
  }

  if (requirementQuery.isError || !requirementQuery.data) {
    return (
      <ErrorState
        title="Authentication is unavailable"
        description={getAuthErrorMessage(
          requirementQuery.error,
          "This knowledge space cannot accept sign-ins right now.",
        )}
        onAction={() => void requirementQuery.refetch()}
      />
    );
  }

  const pending =
    loginMutation.isPending ||
    oidcMutation.isPending ||
    mfaMutation.isPending;

  return (
    <main className="grid min-h-screen place-items-center bg-muted/30 p-4 sm:p-8">
      <Card className="w-full max-w-md rounded-lg">
        <CardHeader className="gap-3 border-b">
          <div className="grid size-10 place-items-center rounded-lg border bg-background">
            <Database className="size-5" />
          </div>
          <div>
            <CardTitle>Knowledge Space sign in</CardTitle>
            <CardDescription className="mt-1">
              Authenticate to continue to this workspace.
            </CardDescription>
          </div>
        </CardHeader>

        <CardContent>
          {challengeId ? (
            <MfaChallengeForm
              pending={mfaMutation.isPending}
              error={error}
              onSubmit={(code) => void handleMfa(code)}
            />
          ) : requirementQuery.data.auth_method === "local" ? (
            <LocalLoginForm
              pending={pending}
              error={error}
              registerHref={`/register?knowledgeSpaceId=${encodeURIComponent(knowledgeSpaceId)}`}
              onSubmit={(credentials) => void handleLocalLogin(credentials)}
            />
          ) : requirementQuery.data.auth_method === "entra" ? (
            <div className="grid gap-4">
              {error && (
                <p role="alert" className="text-sm text-destructive">
                  {error}
                </p>
              )}
              <MicrosoftLoginButton
                pending={oidcMutation.isPending}
                disabled={pending}
                onClick={() => void handleMicrosoftLogin()}
              />
            </div>
          ) : (
            <p role="alert" className="text-sm text-destructive">
              This authentication method is not supported.
            </p>
          )}
        </CardContent>
      </Card>
    </main>
  );
}

function KnowledgeSpaceLoginSkeleton() {
  return (
    <main className="grid min-h-screen place-items-center bg-muted/30 p-4 sm:p-8">
      <div className="grid w-full max-w-md gap-4 rounded-lg border bg-card p-5">
        <Skeleton className="size-10 rounded-lg" />
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-4 w-72 max-w-full" />
        <Skeleton className="mt-3 h-9 w-full" />
      </div>
    </main>
  );
}
