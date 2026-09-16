"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ChevronRight,
  FileText,
  Folder,
  HardDrive,
  Loader2,
  Share2,
} from "lucide-react";

import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import {
  listSharePointDriveChildren,
  listSharePointDrives,
  listSharePointFolderChildren,
  listSharePointSites,
} from "../../api";
import type { DataHubBrowseNode } from "../../types";
import type { IngestionScopeRoot } from "@/modules/ingestion";
import { cn } from "@/lib/utils";

interface DataHubTreeProps {
  selectedRoots: IngestionScopeRoot[];
  onSelectedRootsChange: (
    roots: IngestionScopeRoot[],
  ) => void;
}

export function DataHubTree({
  selectedRoots,
  onSelectedRootsChange,
}: DataHubTreeProps) {
  const [sites, setSites] = useState<DataHubBrowseNode[]>([]);
  const [childrenByKey, setChildrenByKey] = useState<
    Record<string, DataHubBrowseNode[]>
  >({});
  const [expandedKeys, setExpandedKeys] = useState<
    Set<string>
  >(new Set());
  const [loadingKeys, setLoadingKeys] = useState<
    Set<string>
  >(new Set(["root"]));
  const [error, setError] = useState<string | null>(null);

  const selectedKeys = useMemo(
    () => new Set(selectedRoots.map(rootKey)),
    [selectedRoots],
  );

  useEffect(() => {
    let mounted = true;

    async function loadSites() {
      try {
        setError(null);
        setLoadingKeys(new Set(["root"]));
        const data = await listSharePointSites();

        if (mounted) {
          setSites(data);
        }
      } catch (caughtError) {
        if (mounted) {
          setError(toErrorMessage(caughtError));
        }
      } finally {
        if (mounted) {
          setLoadingKeys(new Set());
        }
      }
    }

    void loadSites();

    return () => {
      mounted = false;
    };
  }, []);

  async function toggleExpand(node: DataHubBrowseNode) {
    const key = nodeKey(node);
    const nextExpanded = new Set(expandedKeys);

    if (expandedKeys.has(key)) {
      nextExpanded.delete(key);
      setExpandedKeys(nextExpanded);
      return;
    }

    nextExpanded.add(key);
    setExpandedKeys(nextExpanded);

    if (childrenByKey[key]) {
      return;
    }

    setLoadingKeys((current) => new Set(current).add(key));

    try {
      const children = await loadChildren(node);
      setChildrenByKey((current) => ({
        ...current,
        [key]: children,
      }));
    } catch (caughtError) {
      setError(toErrorMessage(caughtError));
    } finally {
      setLoadingKeys((current) => {
        const next = new Set(current);
        next.delete(key);
        return next;
      });
    }
  }

  function toggleSelection(node: DataHubBrowseNode) {
    const root = toScopeRoot(node);

    if (!root) {
      return;
    }

    const key = rootKey(root);

    if (selectedKeys.has(key)) {
      onSelectedRootsChange(
        selectedRoots.filter(
          (selectedRoot) => rootKey(selectedRoot) !== key,
        ),
      );
      return;
    }

    const withoutChildren = selectedRoots.filter(
      (selectedRoot) =>
        !isCoveredBy(root, selectedRoot) &&
        !isCoveredBy(selectedRoot, root),
    );

    onSelectedRootsChange([...withoutChildren, root]);
  }

  return (
    <div className="rounded-lg border">
      <div className="flex items-center justify-between border-b px-3 py-2">
        <div className="text-sm font-medium">SharePoint</div>
        {loadingKeys.has("root") && (
          <Loader2 className="size-4 animate-spin text-muted-foreground" />
        )}
      </div>

      <div className="max-h-[420px] overflow-auto p-2">
        {error && (
          <p className="px-2 py-3 text-sm text-destructive">
            {error}
          </p>
        )}

        {!error && sites.length === 0 && !loadingKeys.has("root") && (
          <p className="px-2 py-8 text-center text-sm text-muted-foreground">
            No SharePoint sites found.
          </p>
        )}

        {sites.map((site) => (
          <TreeNode
            key={nodeKey(site)}
            node={site}
            depth={0}
            expandedKeys={expandedKeys}
            loadingKeys={loadingKeys}
            childrenByKey={childrenByKey}
            selectedKeys={selectedKeys}
            inheritedSelected={false}
            onExpand={toggleExpand}
            onToggleSelection={toggleSelection}
          />
        ))}
      </div>
    </div>
  );
}

function TreeNode({
  node,
  depth,
  expandedKeys,
  loadingKeys,
  childrenByKey,
  selectedKeys,
  inheritedSelected,
  onExpand,
  onToggleSelection,
}: {
  node: DataHubBrowseNode;
  depth: number;
  expandedKeys: Set<string>;
  loadingKeys: Set<string>;
  childrenByKey: Record<string, DataHubBrowseNode[]>;
  selectedKeys: Set<string>;
  inheritedSelected: boolean;
  onExpand: (node: DataHubBrowseNode) => void;
  onToggleSelection: (node: DataHubBrowseNode) => void;
}) {
  const key = nodeKey(node);
  const root = toScopeRoot(node);
  const selectable = Boolean(root);
  const selected = root ? selectedKeys.has(rootKey(root)) : false;
  const disabled = inheritedSelected && !selected;
  const expanded = expandedKeys.has(key);
  const loading = loadingKeys.has(key);
  const children = childrenByKey[key] ?? [];
  const nextInheritedSelected =
    inheritedSelected || selected;

  return (
    <div>
      <div
        className={cn(
          "flex h-8 items-center gap-2 rounded-md px-2 text-sm",
          disabled && "opacity-50",
        )}
        style={{ paddingLeft: 8 + depth * 18 }}
      >
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="size-6"
          disabled={!node.has_children && node.type !== "site"}
          onClick={() => void onExpand(node)}
        >
          {loading ? (
            <Loader2 className="size-3.5 animate-spin" />
          ) : (
            <ChevronRight
              className={cn(
                "size-3.5 transition-transform",
                expanded && "rotate-90",
              )}
            />
          )}
        </Button>

        {selectable ? (
          <Checkbox
            checked={selected}
            disabled={disabled}
            onCheckedChange={() => onToggleSelection(node)}
          />
        ) : (
          <span className="size-4" />
        )}

        <NodeIcon type={node.type} />
        <span className="min-w-0 truncate">{node.name}</span>
      </div>

      {expanded &&
        children.map((child) => (
          <TreeNode
            key={nodeKey(child)}
            node={child}
            depth={depth + 1}
            expandedKeys={expandedKeys}
            loadingKeys={loadingKeys}
            childrenByKey={childrenByKey}
            selectedKeys={selectedKeys}
            inheritedSelected={nextInheritedSelected}
            onExpand={onExpand}
            onToggleSelection={onToggleSelection}
          />
        ))}
    </div>
  );
}

function NodeIcon({
  type,
}: {
  type: DataHubBrowseNode["type"];
}) {
  if (type === "site") {
    return <Share2 className="size-4 text-sky-600" />;
  }

  if (type === "drive") {
    return <HardDrive className="size-4 text-emerald-600" />;
  }

  if (type === "folder") {
    return <Folder className="size-4 text-amber-600" />;
  }

  return <FileText className="size-4 text-muted-foreground" />;
}

async function loadChildren(node: DataHubBrowseNode) {
  if (node.type === "site" && node.site_id) {
    return listSharePointDrives(node.site_id);
  }

  if (
    node.type === "drive" &&
    node.site_id &&
    node.drive_id
  ) {
    return listSharePointDriveChildren(
      node.site_id,
      node.drive_id,
    );
  }

  if (
    node.type === "folder" &&
    node.site_id &&
    node.drive_id
  ) {
    return listSharePointFolderChildren(
      node.site_id,
      node.drive_id,
      node.id,
    );
  }

  return [];
}

function toScopeRoot(
  node: DataHubBrowseNode,
): IngestionScopeRoot | null {
  if (!node.site_id || !node.drive_id) {
    return null;
  }

  if (node.type === "drive") {
    return {
      site_id: node.site_id,
      drive_id: node.drive_id,
      folder_id: null,
    };
  }

  if (node.type === "folder") {
    return {
      site_id: node.site_id,
      drive_id: node.drive_id,
      folder_id: node.id,
    };
  }

  return null;
}

function isCoveredBy(
  parent: IngestionScopeRoot,
  child: IngestionScopeRoot,
) {
  return (
    parent.site_id === child.site_id &&
    parent.drive_id === child.drive_id &&
    parent.folder_id === null &&
    child.folder_id !== null
  );
}

function nodeKey(node: DataHubBrowseNode) {
  return `${node.type}:${node.site_id ?? ""}:${node.drive_id ?? ""}:${node.id}`;
}

function rootKey(root: IngestionScopeRoot) {
  return `${root.site_id}:${root.drive_id}:${root.folder_id ?? "root"}`;
}

function toErrorMessage(error: unknown) {
  return error instanceof Error
    ? error.message
    : "Unable to load SharePoint.";
}
