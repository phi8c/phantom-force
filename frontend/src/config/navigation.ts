import {
  BarChart3,
  Building2,
  Cpu,
  Database,
  FileText,
  FolderKanban,
  GitBranch,
  KeyRound,
  LayoutDashboard,
  MessageSquare,
  Network,
  Settings,
  ShieldCheck,
  Users,
  Workflow,
} from "lucide-react";

import type { LucideIcon } from "lucide-react";

export interface AdminNavigationItem {
  title: string;
  href: string;
  icon: LucideIcon;
}

export const platformNavigation: AdminNavigationItem[] = [
  {
    title: "Overview",
    href: "/admin",
    icon: LayoutDashboard,
  },
  {
    title: "Enterprises",
    href: "/admin/enterprises",
    icon: Building2,
  },
  {
    title: "Knowledge Spaces",
    href: "/admin/knowledge-spaces",
    icon: Database,
  },
  {
    title: "Members",
    href: "/admin/members",
    icon: Users,
  },
  {
    title: "Roles",
    href: "/admin/roles",
    icon: ShieldCheck,
  },
  {
    title: "Permissions",
    href: "/admin/permissions",
    icon: KeyRound,
  },
  {
    title: "Settings",
    href: "/admin/settings",
    icon: Settings,
  },
];

export function getKnowledgeSpaceNavigation(
  knowledgeSpaceId: string,
): AdminNavigationItem[] {
  const basePath = `/admin/knowledge-spaces/${knowledgeSpaceId}`;

  return [
    {
      title: "Overview",
      href: basePath,
      icon: LayoutDashboard,
    },
    {
      title: "Sources",
      href: `${basePath}/sources`,
      icon: FolderKanban,
    },
    {
      title: "Documents",
      href: `${basePath}/documents`,
      icon: FileText,
    },
    {
      title: "Ingestion",
      href: `${basePath}/ingestion`,
      icon: Workflow,
    },
    {
      title: "Workers",
      href: `${basePath}/workers`,
      icon: Cpu,
    },
    {
      title: "Models",
      href: `${basePath}/models`,
      icon: BarChart3,
    },
    {
      title: "Graph",
      href: `${basePath}/graph`,
      icon: GitBranch,
    },
    {
      title: "Chat",
      href: `${basePath}/chat`,
      icon: MessageSquare,
    },
    {
      title: "Settings",
      href: `${basePath}/settings`,
      icon: Settings,
    },
  ];
}