import Link from "next/link";
import {
  Building2,
  Database,
  KeyRound,
  ShieldCheck,
  Users,
} from "lucide-react";

import { Button } from "@/components/ui/button";

const overviewItems = [
  {
    title: "Enterprises",
    description: "Manage enterprise organizations.",
    href: "/admin/enterprises",
    icon: Building2,
  },
  {
    title: "Knowledge Spaces",
    description: "Manage knowledge spaces and configurations.",
    href: "/admin/knowledge-spaces",
    icon: Database,
  },
  {
    title: "Members",
    description: "Manage users and memberships.",
    href: "/admin/members",
    icon: Users,
  },
  {
    title: "Roles",
    description: "Configure roles across the platform.",
    href: "/admin/roles",
    icon: ShieldCheck,
  },
  {
    title: "Permissions",
    description: "Manage platform permissions.",
    href: "/admin/permissions",
    icon: KeyRound,
  },
];

export default function Page() {
  return (
    <div className="space-y-8 p-6">
      <div>
        <p className="text-sm font-medium text-muted-foreground">
          Platform Administration
        </p>

        <h1 className="mt-1 text-2xl font-semibold tracking-tight">
          Welcome to Phantom Force
        </h1>

        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          Manage enterprises, knowledge spaces, users, roles,
          permissions, and platform-level configurations.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {overviewItems.map((item) => {
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className="group rounded-xl border bg-card p-5 transition-colors hover:border-primary/50 hover:bg-accent/30"
            >
              <div className="flex size-10 items-center justify-center rounded-lg bg-muted text-foreground">
                <Icon className="size-5" />
              </div>

              <h2 className="mt-4 font-semibold">
                {item.title}
              </h2>

              <p className="mt-1 text-sm text-muted-foreground">
                {item.description}
              </p>

              <p className="mt-4 text-sm font-medium text-primary">
                Manage →
              </p>
            </Link>
          );
        })}
      </div>

      <div className="rounded-xl border border-dashed p-6">
        <h2 className="font-semibold">
          Getting started
        </h2>

        <p className="mt-2 text-sm text-muted-foreground">
          Create an enterprise first, then create a knowledge
          space inside that enterprise to start managing your
          knowledge platform.
        </p>

       
      </div>
    </div>
  );
}