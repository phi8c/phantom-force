import type { IngestionScopeRoot } from "../../../ingestion/types/ingestion.types";

export type GenericScopeRoot = Extract<
  IngestionScopeRoot,
  { locator: Record<string, unknown> }
>;

export function isGenericRoot(
  root: IngestionScopeRoot,
): root is GenericScopeRoot {
  return "locator" in root;
}

export function genericRootKey(root: GenericScopeRoot) {
  return stableSerialize(root.locator);
}

export function selectedGenericKeys(roots: IngestionScopeRoot[]) {
  return new Set(roots.filter(isGenericRoot).map(genericRootKey));
}

export function selectGenericRoot(
  selectedRoots: IngestionScopeRoot[],
  root: GenericScopeRoot,
  descendantKeys: ReadonlySet<string>,
) {
  const rootKey = genericRootKey(root);
  const preserved = selectedRoots.filter((selectedRoot) => {
    if (!isGenericRoot(selectedRoot)) {
      return true;
    }
    const selectedKey = genericRootKey(selectedRoot);
    return selectedKey !== rootKey && !descendantKeys.has(selectedKey);
  });
  return [...preserved, root];
}

export function deselectGenericRoot(
  selectedRoots: IngestionScopeRoot[],
  root: GenericScopeRoot,
) {
  const key = genericRootKey(root);
  return selectedRoots.filter(
    (selectedRoot) =>
      !isGenericRoot(selectedRoot) || genericRootKey(selectedRoot) !== key,
  );
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
