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
  browseDataHubChildren,
  browseDataHubRoot,
} from "../../api";
import type { DataHubBrowseNode } from "../../types";
import type { IngestionScopeRoot } from "@/modules/ingestion";
import { cn } from "@/lib/utils";

interface DataHubTreeProps {
  knowledgeSpaceId: string;
  selectedRoots: IngestionScopeRoot[];
  onSelectedRootsChange: (
    roots: IngestionScopeRoot[],
  ) => void;
}

export function DataHubTree({
  knowledgeSpaceId,
  selectedRoots,
  onSelectedRootsChange,
}: DataHubTreeProps) {
  return (
    <DataHubTreeContent
      key={knowledgeSpaceId}
      knowledgeSpaceId={knowledgeSpaceId}
      selectedRoots={selectedRoots}
      onSelectedRootsChange={onSelectedRootsChange}
    />
  );
}

function DataHubTreeContent({
  knowledgeSpaceId,
  selectedRoots,
  onSelectedRootsChange,
}: DataHubTreeProps) {
  const [rootNodes, setRootNodes] = useState<DataHubBrowseNode[]>([]);
  const [provider, setProvider] = useState<string | null>(null);
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
    () =>
      new Set(
        selectedRoots
          .filter(isGenericRoot)
          .map(rootKey),
      ),
    [selectedRoots],
  );

  useEffect(() => {
    let mounted = true;

    async function loadRoot() {
      try {
        const data = await browseDataHubRoot(knowledgeSpaceId);

        if (mounted) {
          setRootNodes(data.nodes);
          setProvider(data.provider);
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

    void loadRoot();

    return () => {
      mounted = false;
    };
  }, [knowledgeSpaceId]);

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
      const response = await browseDataHubChildren(
        knowledgeSpaceId,
        node.locator,
      );
      setChildrenByKey((current) => ({
        ...current,
        [key]: response.nodes,
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
        selectedRoots.filter(isGenericRoot).filter(
          (selectedRoot) => rootKey(selectedRoot) !== key,
        ),
      );
      return;
    }

    const descendantKeys = collectDescendantRootKeys(
      node,
      childrenByKey,
    );
    const withoutChildren = selectedRoots
      .filter(isGenericRoot)
      .filter(
        (selectedRoot) =>
          !descendantKeys.has(rootKey(selectedRoot)),
      );

    onSelectedRootsChange([...withoutChildren, root]);
  }

  return (
    <div className="rounded-lg border">
      <div className="flex items-center justify-between border-b px-3 py-2">
        <div className="text-sm font-medium">
          {provider ? formatProvider(provider) : "Data Hub"}
        </div>
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

        {!error && rootNodes.length === 0 && !loadingKeys.has("root") && (
          <p className="px-2 py-8 text-center text-sm text-muted-foreground">
            No Data Hub items found.
          </p>
        )}

        {rootNodes.map((node) => (
          <TreeNode
            key={nodeKey(node)}
            node={node}
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
          disabled={!node.has_children}
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

function toScopeRoot(
  node: DataHubBrowseNode,
): IngestionScopeRoot | null {
  if (node.type === "drive" || node.type === "folder") {
    return { locator: { ...node.locator } };
  }

  return null;
}

function nodeKey(node: DataHubBrowseNode) {
  return `${node.provider}:${node.type}:${node.id}`;
}

function rootKey(root: IngestionScopeRoot) {
  if (!isGenericRoot(root)) {
    return "legacy";
  }

  return stableSerialize(root.locator);
}

function isGenericRoot(
  root: IngestionScopeRoot,
): root is Extract<IngestionScopeRoot, { locator: Record<string, unknown> }> {
  return "locator" in root;
}

function collectDescendantRootKeys(
  node: DataHubBrowseNode,
  childrenByKey: Record<string, DataHubBrowseNode[]>,
) {
  const keys = new Set<string>();
  const pending = [...(childrenByKey[nodeKey(node)] ?? [])];

  while (pending.length > 0) {
    const child = pending.pop();
    if (!child) {
      continue;
    }
    const root = toScopeRoot(child);
    if (root) {
      keys.add(rootKey(root));
    }
    pending.push(...(childrenByKey[nodeKey(child)] ?? []));
  }

  return keys;
}

function stableSerialize(value: unknown): string {
  if (Array.isArray(value)) {
    return `[${value.map(stableSerialize).join(",")}]`;
  }
  if (value !== null && typeof value === "object") {
    const record = value as Record<string, unknown>;
    return `{${Object.keys(record)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${stableSerialize(record[key])}`)
      .join(",")}}`;
  }
  return JSON.stringify(value) ?? "undefined";
}

function formatProvider(provider: string) {
  return provider
    .split(/[_-]/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function toErrorMessage(error: unknown) {
  return error instanceof Error
    ? error.message
    : "Unable to load Data Hub.";
}
