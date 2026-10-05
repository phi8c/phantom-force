"use client";

import { useEffect, type ReactNode } from "react";
import { useParams, usePathname, useRouter } from "next/navigation";

import { ErrorState } from "@/components/shared/error-state";

import { isUnauthorizedAuthError } from "../auth-errors";
import { useCurrentUser } from "../hooks";
import { isKnowledgeSpaceSession } from "../session-context";
import { AuthLoadingState } from "./AuthLoadingState";

interface KnowledgeSpaceAuthBoundaryProps {
  children: ReactNode;
}

export function KnowledgeSpaceAuthBoundary({
  children,
}: KnowledgeSpaceAuthBoundaryProps) {
  const params = useParams<{ knowledgeSpaceId: string }>();
  const pathname = usePathname();
  const router = useRouter();
  const knowledgeSpaceId = params.knowledgeSpaceId;
  const loginPath = `/chat/${encodeURIComponent(knowledgeSpaceId)}/login`;
  const chatPath = `/chat/${encodeURIComponent(knowledgeSpaceId)}`;
  const isLoginRoute = pathname === loginPath;
  const sessionQuery = useCurrentUser();
  const hasMatchingSession = isKnowledgeSpaceSession(
    sessionQuery.data,
    knowledgeSpaceId,
  );
  const isUnauthenticated = isUnauthorizedAuthError(sessionQuery.error);

  useEffect(() => {
    if (sessionQuery.isLoading) {
      return;
    }

    if (isLoginRoute && hasMatchingSession) {
      router.replace(chatPath);
      return;
    }

    if (
      !isLoginRoute &&
      !hasMatchingSession &&
      (isUnauthenticated || Boolean(sessionQuery.data))
    ) {
      router.replace(loginPath);
    }
  }, [
    chatPath,
    hasMatchingSession,
    isLoginRoute,
    isUnauthenticated,
    loginPath,
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
    return hasMatchingSession ? <AuthLoadingState /> : children;
  }

  return hasMatchingSession ? children : <AuthLoadingState />;
}
