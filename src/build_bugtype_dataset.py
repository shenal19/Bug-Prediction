import re
import json
from pathlib import Path
from typing import List, Dict

import pandas as pd

from .code_scanner import extract_metrics_lizard


SUPPORTED_EXTS = (".py", ".java", ".c", ".cpp")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _count(text: str, token: str) -> int:
    return text.count(token)


def _estimate_python_max_indent_spaces(text: str) -> int:
    max_indent = 0
    for line in text.splitlines():
        if not line.strip():
            continue
        leading = len(line) - len(line.lstrip(" \t"))
        if leading > max_indent:
            max_indent = leading
    return max_indent


def _estimate_brace_depth(text: str) -> int:
    depth = 0
    max_depth = 0
    for ch in text:
        if ch == '{':
            depth += 1
            if depth > max_depth:
                max_depth = depth
        elif ch == '}':
            depth = max(0, depth - 1)
    return max_depth


def _derive_bug_type(ext: str, metrics: Dict, extras: Dict) -> str:
    complexity = float(metrics.get("v(g)", 0))
    loc = int(metrics.get("loc", 1))
    branch = int(metrics.get("branchCount", 0))
    imports = int(extras.get("imports_count", 0))
    includes = int(extras.get("includes_count", 0))
    pointer_ops = bool(extras.get("pointer_ops", False))
    null_checks = int(extras.get("null_checks", 0))
    brace_depth = int(extras.get("brace_depth", 0))
    py_indent = int(extras.get("py_max_indent", 0))

    if ext in (".c", ".cpp") and pointer_ops and (complexity >= 6 or brace_depth >= 3):
        return "pointer/control-flow"
    if ext in (".java", ".c", ".cpp") and null_checks > 0 and complexity >= 3:
        return "null-check"
    if ext == ".java" and loc >= 200:
        return "bloat/long-class"
    if ext == ".py" and py_indent >= 12 and complexity >= 4:
        return "nested-logic"
    if complexity >= 6 or brace_depth >= 4:
        return "logic/complexity"
    if (imports + includes) >= 8 or (imports >= 5 and branch >= 10):
        return "coupling/dependency"
    return "general/maintainability"


def build_dataset(source_dir: str, out_csv: str, exts: List[str] = None) -> pd.DataFrame:
    root = Path(source_dir)
    if exts is None:
        exts = list(SUPPORTED_EXTS)
    rows = []
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        if f.suffix.lower() not in exts:
            continue
        text = _read_text(f)
        metrics = extract_metrics_lizard(str(f))

        # Extras by language
        ext = f.suffix.lower()
        imports_count = 0
        includes_count = 0
        null_checks = 0
        pointer_ops = False
        brace_depth = 0
        py_max_indent = 0

        if ext == ".py":
            imports_count = sum(1 for line in text.splitlines() if line.strip().startswith("import ") or line.strip().startswith("from "))
            py_max_indent = _estimate_python_max_indent_spaces(text)
        else:
            if ext == ".java":
                imports_count = _count(text, "import ")
            if ext in (".c", ".cpp"):
                includes_count = _count(text, "#include ")
                if ("->" in text) or re.search(r"\*[A-Za-z_]\w*\s*\*", text):
                    pointer_ops = True
            null_checks = _count(text, "== null") + _count(text, "!= null")
            brace_depth = _estimate_brace_depth(text)

        extras = {
            "imports_count": imports_count,
            "includes_count": includes_count,
            "null_checks": null_checks,
            "pointer_ops": pointer_ops,
            "brace_depth": brace_depth,
            "py_max_indent": py_max_indent,
        }

        bug_type = _derive_bug_type(ext, metrics, extras)
        row = {"file": str(f), **metrics, **extras, "bug_type": bug_type}
        rows.append(row)

    df = pd.DataFrame(rows)
    if out_csv:
        Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_csv, index=False)
    return df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build a heuristic bug-type dataset from a source tree.")
    parser.add_argument("--source", required=True, help="Folder containing source files")
    parser.add_argument("--out", required=True, help="Output CSV path")
    parser.add_argument("--exts", nargs="*", help="Optional list of extensions (e.g., .py .java .c .cpp)")
    args = parser.parse_args()
    exts = args.exts if args.exts else None
    df = build_dataset(args.source, args.out, exts)
    print(json.dumps({"rows": int(len(df)), "out": args.out}, indent=2))


