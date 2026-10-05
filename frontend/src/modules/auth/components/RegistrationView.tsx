"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, Eye, EyeOff, LoaderCircle, UserPlus } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { getAuthErrorMessage } from "../auth-errors";
import { useRegisterLocalUser } from "../hooks";

export function RegistrationView() {
  const searchParams = useSearchParams();
  const registrationMutation = useRegisterLocalUser();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const knowledgeSpaceId = searchParams.get("knowledgeSpaceId");
  const signInPath = knowledgeSpaceId
    ? `/chat/${encodeURIComponent(knowledgeSpaceId)}/login`
    : "/admin/login";
  const canSubmit =
    email.trim().length > 0 &&
    password.length >= 12 &&
    password === confirmPassword &&
    !registrationMutation.isPending;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!canSubmit) {
      return;
    }

    setError(null);
    setMessage(null);

    try {
      const result = await registrationMutation.mutateAsync({
        email: email.trim(),
        password,
      });
      setMessage(result.message);
    } catch (caughtError) {
      setError(getAuthErrorMessage(caughtError, "Registration failed."));
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-muted/30 p-4 sm:p-8">
      <Card className="w-full max-w-md rounded-lg">
        <CardHeader className="gap-3 border-b">
          <div className="grid size-10 place-items-center rounded-lg border bg-background">
            <UserPlus className="size-5" />
          </div>
          <div>
            <CardTitle>Create an account</CardTitle>
            <CardDescription className="mt-1">
              Register with your email and a secure password.
            </CardDescription>
          </div>
        </CardHeader>

        <CardContent>
          {message ? (
            <div className="grid gap-4 text-center">
              <CheckCircle2 className="mx-auto size-9 text-foreground" />
              <p className="text-sm text-muted-foreground">{message}</p>
              <Button
                render={<Link href={signInPath} />}
                nativeButton={false}
                variant="outline"
              >
                Return to sign in
              </Button>
            </div>
          ) : (
            <form className="grid gap-4" onSubmit={handleSubmit}>
              <div className="grid gap-2">
                <Label htmlFor="registration-email">Email</Label>
                <Input
                  id="registration-email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  maxLength={320}
                  value={email}
                  disabled={registrationMutation.isPending}
                  required
                  onChange={(event) => setEmail(event.target.value)}
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="registration-password">Password</Label>
                <div className="relative">
                  <Input
                    id="registration-password"
                    name="new-password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="new-password"
                    minLength={12}
                    className="pr-10"
                    value={password}
                    disabled={registrationMutation.isPending}
                    required
                    onChange={(event) => setPassword(event.target.value)}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon-sm"
                    className="absolute right-0.5 top-0.5"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    aria-pressed={showPassword}
                    onClick={() => setShowPassword((visible) => !visible)}
                  >
                    <EyeOff className={showPassword ? undefined : "hidden"} />
                    <Eye className={showPassword ? "hidden" : undefined} />
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  Use at least 12 characters.
                </p>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="registration-password-confirm">
                  Confirm password
                </Label>
                <Input
                  id="registration-password-confirm"
                  name="confirm-password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="new-password"
                  minLength={12}
                  value={confirmPassword}
                  disabled={registrationMutation.isPending}
                  required
                  aria-invalid={
                    confirmPassword.length > 0 && password !== confirmPassword
                  }
                  onChange={(event) => setConfirmPassword(event.target.value)}
                />
              </div>

              {error && (
                <p role="alert" className="text-sm text-destructive">
                  {error}
                </p>
              )}

              <Button type="submit" size="lg" disabled={!canSubmit}>
                <LoaderCircle
                  className={registrationMutation.isPending ? "animate-spin" : "hidden"}
                />
                <UserPlus
                  className={registrationMutation.isPending ? "hidden" : undefined}
                />
                <span className={registrationMutation.isPending ? undefined : "hidden"}>
                  Creating account...
                </span>
                <span className={registrationMutation.isPending ? "hidden" : undefined}>
                  Create account
                </span>
              </Button>

              <p className="text-center text-sm text-muted-foreground">
                Already registered?{" "}
                <Link
                  href={signInPath}
                  className="font-medium text-foreground underline-offset-4 hover:underline"
                >
                  Sign in
                </Link>
              </p>
            </form>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
