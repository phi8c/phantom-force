import assert from "node:assert/strict";
import test from "node:test";

import type { IngestionScopeRoot } from "../../../ingestion/types/ingestion.types";
import {
  deselectGenericRoot,
  genericRootKey,
  selectGenericRoot,
  selectedGenericKeys,
} from "./selection.ts";

const legacy: IngestionScopeRoot = {
  site_id: "site",
  drive_id: "drive",
  folder_id: null,
};
const rootA = { locator: { path: "/A" } };
const rootB = { locator: { path: "/B" } };
const child = { locator: { path: "/A/child" } };

test("legacy-only roots do not crash generic key selection", () => {
  assert.deepEqual([...selectedGenericKeys([legacy])], []);
});

test("deselecting a generic root preserves legacy roots", () => {
  assert.deepEqual(deselectGenericRoot([legacy, rootA], rootA), [legacy]);
});

test("selecting another generic root preserves legacy roots", () => {
  assert.deepEqual(
    selectGenericRoot([legacy, rootA], rootB, new Set()),
    [legacy, rootA, rootB],
  );
});

test("descendant cleanup only removes matching generic descendants", () => {
  assert.deepEqual(
    selectGenericRoot(
      [legacy, child, rootB],
      rootA,
      new Set([genericRootKey(child)]),
    ),
    [legacy, rootB, rootA],
  );
});
