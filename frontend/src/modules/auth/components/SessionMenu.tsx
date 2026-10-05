"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { LogOut, UserRoundX } from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import { getAuthErrorMessage } from "../auth-errors";
import { useCurrentUser, useLogout, useLogoutAllSessions } from "../hooks";

interface SessionMenuProps {
  signedOutPath: string;
}

export function SessionMenu({ signedOutPath }: SessionMenuProps) {
  const router = useRouter();
  const sessionQuery = useCurrentUser();
  const logoutMutation = useLogout();
  const logoutAllMutation = useLogoutAllSessions();
  const [error, setError] = useState<string | null>(null);
  const pending = logoutMutation.isPending || logoutAllMutation.isPending;
  const email = sessionQuery.data?.email ?? "Account";

  async function handleLogout(allSessions: boolean) {
    setError(null);

    try {
      if (allSessions) {
        await logoutAllMutation.mutateAsync();
      } else {
        await logoutMutation.mutateAsync();
      }
      router.replace(signedOutPath);
    } catch (caughtError) {
      setError(getAuthErrorMessage(caughtError, "Sign out failed."));
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label="Open account menu"
          />
        }
      >
        <Avatar>
          <AvatarFallback>{email.slice(0, 1).toUpperCase()}</AvatarFallback>
        </Avatar>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuLabel className="truncate">{email}</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {error && (
          <div role="alert" className="px-1.5 py-1 text-xs text-destructive">
            {error}
          </div>
        )}
        <DropdownMenuItem
          disabled={pending}
          onClick={() => void handleLogout(false)}
        >
          <LogOut />
          Sign out
        </DropdownMenuItem>
        <DropdownMenuItem
          variant="destructive"
          disabled={pending}
          onClick={() => void handleLogout(true)}
        >
          <UserRoundX />
          Sign out all sessions
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
