import { Suspense } from "react";

import { AuthLoadingState, RegistrationView } from "@/modules/auth";

export default function RegistrationPage() {
  return (
    <Suspense fallback={<AuthLoadingState />}>
      <RegistrationView />
    </Suspense>
  );
}
