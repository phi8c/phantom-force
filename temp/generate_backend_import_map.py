import ast
from pathlib import Path
from collections import defaultdict
from datetime import datetime

ROOT = Path(r"d:\pico_azure_rag\backend")
OUT_MD = Path(r"d:\pico_azure_rag\document\backend_import_map.md")
OUT_JSON = Path(r"d:\pico_azure_rag\document\backend_import_map.json")


def build_module_index(files):
    module_map = {}
    for file_path in files:
        rel = file_path.relative_to(ROOT)
        parts = list(rel.with_suffix("").parts)
        if file_path.name == "__init__.py":
            # package module name from parent directory
            if len(parts) >= 2:
                module_name = ".".join(parts[:-1])
            else:
                module_name = ""
        else:
            module_name = ".".join(parts)
        if module_name:
            module_map[module_name] = file_path

    # add parent package modules for directories that are packages
    for file_path in files:
        if file_path.name == "__init__.py":
            rel = file_path.relative_to(ROOT)
            parent_parts = list(rel.parent.parts)
            package_name = ".".join(parent_parts)
            if package_name and package_name not in module_map:
                module_map[package_name] = file_path
    return module_map


def resolve_import_path(importing_file, module_name, level, module_map):
    if not module_name:
        return None

    rel = importing_file.relative_to(ROOT)
    if importing_file.name == "__init__.py":
        pkg_parts = list(rel.parent.parts)
    else:
        pkg_parts = list(rel.with_suffix("").parent.parts)

    if level > 0:
        if level == 1:
            base_parts = pkg_parts
        else:
            base_parts = pkg_parts[: max(0, len(pkg_parts) - (level - 1))]
        target_parts = base_parts + module_name.split(".") if module_name else base_parts
        target_name = ".".join(target_parts)
    else:
        target_name = module_name

    # exact module match
    if target_name in module_map:
        return module_map[target_name]

    # try package path by suffix if module references a submodule that is a package
    candidate = target_name
    while candidate:
        if candidate in module_map:
            return module_map[candidate]
        candidate = ".".join(candidate.split(".")[:-1])

    # also try relative to repo root as a file path if the module name points to a subpackage
    candidate_path = ROOT.joinpath(*target_name.split("."))
    if candidate_path.exists() and candidate_path.is_dir():
        init_py = candidate_path / "__init__.py"
        if init_py.exists():
            return init_py
    if candidate_path.exists() and candidate_path.suffix == ".py":
        return candidate_path
    return None


def parse_file_imports(file_path):
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    except Exception:
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, 0))
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            imports.append((module_name, node.level))
    return imports


def normalize_path(path):
    return path.relative_to(ROOT).as_posix()


python_files = sorted([p for p in ROOT.rglob("*.py") if "__pycache__" not in p.parts and ".venv" not in p.parts])
module_map = build_module_index(python_files)

edges = []
reverse = defaultdict(list)

for file_path in python_files:
    rel = normalize_path(file_path)
    imports = parse_file_imports(file_path)
    for module_name, level in imports:
        target_path = resolve_import_path(file_path, module_name, level, module_map)
        if target_path is None:
            continue
        target_rel = normalize_path(target_path)
        if target_rel == rel:
            continue
        edges.append((rel, target_rel))
        reverse[target_rel].append(rel)

# Deduplicate and sort
edges = sorted(set(edges))
for target_rel in reverse:
    reverse[target_rel] = sorted(set(reverse[target_rel]))

# Write JSON
payload = {
    "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    "python_files": len(python_files),
    "internal_import_edges": len(edges),
    "edges": [{"from": src, "to": dst} for src, dst in edges],
    "reverse": {target: sorted(importers) for target, importers in sorted(reverse.items())},
}
OUT_JSON.write_text(__import__("json").dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

# Write markdown
lines = []
lines.append("# Backend import map")
lines.append("")
lines.append(f"Generated at: {payload['generated_at']}")
lines.append(f"Python files scanned: {payload['python_files']}")
lines.append(f"Internal import edges: {payload['internal_import_edges']}")
lines.append("")
lines.append("## 1. File-to-file import relations")
lines.append("")
for src, dst in edges:
    lines.append(f"- {src} -> {dst}")
lines.append("")
lines.append("## 2. Reverse dependency index")
lines.append("")
for target in sorted(reverse):
    importers = reverse[target]
    lines.append(f"### {target}")
    for importer in importers:
        lines.append(f"- imported by: {importer}")
    lines.append("")

OUT_MD.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {OUT_MD}")
print(f"Wrote {OUT_JSON}")
print(f"Scanned {len(python_files)} Python files")
print(f"Found {len(edges)} internal import edges")
