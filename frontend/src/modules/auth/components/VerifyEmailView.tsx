"use client";

import { useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, LoaderCircle, MailCheck } from "lucide-react";

import { ErrorState } from "@/components/shared/error-state";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import { getAuthErrorMessage } from "../auth-errors";
import { useVerifyEmail } from "../hooks";

export function VerifyEmailView() {
  const searchParams = useSearchParams();
  const verifyMutation = useVerifyEmail();
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const token = searchParams.get("token");

  async function handleVerify() {
    if (!token) {
      return;
    }

    setError(null);
    try {
      const result = await verifyMutation.mutateAsync({ token });
      setMessage(result.message);
    } catch (caughtError) {
      setError(getAuthErrorMessage(caughtError, "Email verification failed."));
    }
  }

  if (!token || token.length < 32) {
    return (
      <ErrorState
        title="Invalid verification link"
        description="The verification token is missing or incomplete."
      />
    );
  }

  return (
    <main className="grid min-h-screen place-items-center bg-muted/30 p-4 sm:p-8">
      <Card className="w-full max-w-md rounded-lg">
        <CardHeader className="gap-3 border-b">
          <div className="grid size-10 place-items-center rounded-lg border bg-background">
            {message ? <CheckCircle2 className="size-5" /> : <MailCheck className="size-5" />}
          </div>
          <div>
            <CardTitle>Verify your email</CardTitle>
            <CardDescription className="mt-1">
              Confirm your email address to activate your account.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="grid gap-4">
          {message ? (
            <>
              <p className="text-sm text-muted-foreground">{message}</p>
              <Button
                render={<Link href="/admin/login" />}
                nativeButton={false}
              >
                Continue to sign in
              </Button>
            </>
          ) : (
            <>
              {error && (
                <p role="alert" className="text-sm text-destructive">
                  {error}
                </p>
              )}
              <Button
                type="button"
                size="lg"
                disabled={verifyMutation.isPending}
                onClick={() => void handleVerify()}
              >
                <LoaderCircle
                  className={verifyMutation.isPending ? "animate-spin" : "hidden"}
                />
                <MailCheck
                  className={verifyMutation.isPending ? "hidden" : undefined}
                />
                <span className={verifyMutation.isPending ? undefined : "hidden"}>
                  Verifying...
                </span>
                <span className={verifyMutation.isPending ? "hidden" : undefined}>
                  Verify email
                </span>
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
