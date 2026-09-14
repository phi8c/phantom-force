import { AdminHeaderActions } from "./AdminHeaderActions";
import { AdminHeaderTitle } from "./AdminHeaderTitle";

export function AdminHeader() {
  return (
    <header className="flex h-12 shrink-0 items-center justify-between border-b bg-background px-6">
      <AdminHeaderTitle />

      <AdminHeaderActions />
    </header>
  );
}