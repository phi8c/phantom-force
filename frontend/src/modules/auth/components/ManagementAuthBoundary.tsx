"use client";

import { useEffect, type ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";

import { AdminShell } from "@/components/layout/admin-shell/AdminShell";
import { ErrorState } from "@/components/shared/error-state";

import { isUnauthorizedAuthError } from "../auth-errors";
import { useCurrentUser } from "../hooks";
import { isManagementSession } from "../session-context";
import { AuthLoadingState } from "./AuthLoadingState";
import { SessionMenu } from "./SessionMenu";

interface ManagementAuthBoundaryProps {
  children: ReactNode;
}

const MANAGEMENT_LOGIN_PATH = "/admin/login";

export function ManagementAuthBoundary({
  children,
}: ManagementAuthBoundaryProps) {
  const pathname = usePathname();
  const router = useRouter();
  const sessionQuery = useCurrentUser();
  const isLoginRoute = pathname === MANAGEMENT_LOGIN_PATH;
  const hasManagementSession = isManagementSession(sessionQuery.data);
  const isUnauthenticated = isUnauthorizedAuthError(sessionQuery.error);

  useEffect(() => {
    if (sessionQuery.isLoading) {
      return;
    }

    if (isLoginRoute && hasManagementSession) {
      router.replace("/admin");
      return;
    }

    if (
      !isLoginRoute &&
      !hasManagementSession &&
      (isUnauthenticated || Boolean(sessionQuery.data))
    ) {
      router.replace(MANAGEMENT_LOGIN_PATH);
    }
  }, [
    hasManagementSession,
    isLoginRoute,
    isUnauthenticated,
    router,
    sessionQuery.data,
    sessionQuery.isLoading,
  ]);

  if (sessionQuery.isLoading) {
    return <AuthLoadingState />;
  }

  if (sessionQuery.isError && !isUnauthenticated) {
    return (
      <ErrorState
        title="Unable to verify your session"
        description="The authentication service could not be reached."
        onAction={() => void sessionQuery.refetch()}
      />
    );
  }

  if (isLoginRoute) {
    return hasManagementSession ? <AuthLoadingState /> : children;
  }

  if (!hasManagementSession) {
    return <AuthLoadingState />;
  }

  return (
    <AdminShell
      accountAction={<SessionMenu signedOutPath={MANAGEMENT_LOGIN_PATH} />}
    >
      {children}
    </AdminShell>
  );
}
