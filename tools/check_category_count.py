#!/usr/bin/env python3
"""Guard the load-bearing "N categories" constant against drift.

The number of strictify categories is quoted in four places -- the skill, the
README, and both plugin manifests -- and ARCHITECTURE.md calls it out as a
shared constant. This hook takes the count of numbered category items in
SKILL.md as the source of truth and fails if any prose mention disagrees.

Reports violations as `{file}:{line}: {message} -- {remediation}` and exits
non-zero on mismatch, matching this repo's hook-output convention.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / "skills" / "strictify" / "SKILL.md"

# Files that quote the category count in prose/metadata.
MENTION_FILES = [
    SKILL,
    REPO_ROOT / "README.md",
    REPO_ROOT / ".claude-plugin" / "plugin.json",
    REPO_ROOT / ".claude-plugin" / "marketplace.json",
]

# Matches "22 categories" and "22 strictness categories".
_MENTION_RE = re.compile(r"\b(\d+)\s+(?:strictness\s+)?categories\b")
# Matches a top-level numbered category item, e.g. "14. **Architecture codemap**".
_ITEM_RE = re.compile(r"^(\d+)\.\s+\*\*")


def _numbered_items(skill_text: str) -> list[int]:
    return [int(m.group(1)) for line in skill_text.splitlines() if (m := _ITEM_RE.match(line))]


def main() -> int:
    skill_text = SKILL.read_text(encoding="utf-8")
    items = _numbered_items(skill_text)

    violations: list[str] = []

    expected = list(range(1, len(items) + 1))
    if items != expected:
        violations.append(
            f"{SKILL.relative_to(REPO_ROOT)}:1: numbered categories are {items}, "
            f"not a contiguous 1..{len(items)} sequence -- fix the numbering so the "
            "list is sequential"
        )

    truth = len(items)

    for path in MENTION_FILES:
        rel = path.relative_to(REPO_ROOT)
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for m in _MENTION_RE.finditer(line):
                found = int(m.group(1))
                if found != truth:
                    violations.append(
                        f"{rel}:{lineno}: says '{found} categories' but SKILL.md defines "
                        f"{truth} -- update this mention to {truth} (or add/remove a category)"
                    )

    for v in violations:
        print(v)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
