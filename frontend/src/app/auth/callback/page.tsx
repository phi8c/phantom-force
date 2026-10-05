import { Suspense } from "react";

import { AuthCallbackView, AuthLoadingState } from "@/modules/auth";

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={<AuthLoadingState />}>
      <AuthCallbackView />
    </Suspense>
  );
}
