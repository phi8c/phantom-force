"use client";

import { usePathname } from "next/navigation";

import {
  getKnowledgeSpaceNavigation,
  platformNavigation,
  type AdminNavigationItem,
} from "@/config/navigation";

import { AdminSidebarNavigationItem } from "./AdminSidebarNavigationItem";

export function AdminSidebarNavigation() {
  const pathname = usePathname();

  const knowledgeSpaceId = getKnowledgeSpaceIdFromPath(pathname);

  const navigationItems = knowledgeSpaceId
    ? getKnowledgeSpaceNavigation(knowledgeSpaceId)
    : platformNavigation;

  return (
    <nav className="flex-1 space-y-1 overflow-y-auto p-3">
      {navigationItems.map((item) => (
        <AdminSidebarNavigationItem
          key={item.href}
          title={item.title}
          href={item.href}
          icon={item.icon}
          active={isNavigationItemActive(pathname, item)}
        />
      ))}
    </nav>
  );
}

function getKnowledgeSpaceIdFromPath(
  pathname: string,
): string | null {
  const pathSegments = pathname.split("/").filter(Boolean);

  const knowledgeSpacesIndex = pathSegments.indexOf(
    "knowledge-spaces",
  );

  if (knowledgeSpacesIndex === -1) {
    return null;
  }

  const knowledgeSpaceId =
    pathSegments[knowledgeSpacesIndex + 1];

  if (!knowledgeSpaceId) {
    return null;
  }

  return knowledgeSpaceId;
}

function isNavigationItemActive(
  pathname: string,
  item: AdminNavigationItem,
): boolean {
  if (item.href === "/admin") {
    return pathname === "/admin";
  }

  return pathname === item.href || pathname.startsWith(`${item.href}/`);
}