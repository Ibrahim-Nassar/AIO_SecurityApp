import os
import re
import sys
from pathlib import Path

# Patterns to scan (very lightweight):
PATTERNS = [
    re.compile(r"\beval\s*\("),
    re.compile(r"\bexec\s*\("),
    re.compile(r"pickle\.load\s*\("),
    re.compile(r"yaml\.load\s*\(.*\)"),  # allow but will flag unless SafeLoader is mentioned on line
    re.compile(r"subprocess\.Popen\s*\(.*shell\s*=\s*True"),
]

ALLOW_IF_SAFE = re.compile(r"yaml\.load\(.*SafeLoader")

ROOT = Path(__file__).resolve().parents[1]


def should_skip(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    if rel.startswith("tests/"):
        return True
    if "/.venv/" in rel or rel.startswith(".git/"):
        return True
    return False


def main() -> int:
    hits: list[tuple[str, int, str]] = []
    for dirpath, _, filenames in os.walk(ROOT):
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            p = Path(dirpath) / fn
            try:
                if should_skip(p):
                    continue
            except Exception:
                continue
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for ln_no, line in enumerate(f, start=1):
                        text = line.rstrip("\n")
                        # Special case: allow yaml.load(..., Loader=SafeLoader)
                        if "yaml.load(" in text and "SafeLoader" in text:
                            continue
                        for rx in PATTERNS:
                            if rx.search(text):
                                hits.append((str(p.relative_to(ROOT)), ln_no, text.strip()))
                                break
            except Exception:
                # skip unreadable files
                continue
    if hits:
        print("Static security check found potentially dangerous usage:")
        for path, ln, text in hits:
            print(f"{path}:{ln}: {text}")
        return 2
    print("Static security check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main()) 