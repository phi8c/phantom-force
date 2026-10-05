import { Suspense } from "react";

import { AuthLoadingState, VerifyEmailView } from "@/modules/auth";

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<AuthLoadingState />}>
      <VerifyEmailView />
    </Suspense>
  );
}
