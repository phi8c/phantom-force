import { AdminSidebarFooter } from "./AdminSidebarFooter";
import { AdminSidebarHeader } from "./AdminSidebarHeader";
import { AdminSidebarNavigation } from "./AdminSidebarNavigation";

export function AdminSidebar() {
  return (
    <aside className="group flex h-screen w-16 shrink-0 flex-col border-r bg-sidebar transition-[width] duration-200 ease-in-out hover:w-64">
      <AdminSidebarHeader />
      <AdminSidebarNavigation />
      <AdminSidebarFooter />
    </aside>
  );
}