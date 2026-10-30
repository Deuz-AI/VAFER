# tests/skillcheck.py
"""Shared helpers for the per-skill hygiene tests (not a test module)."""

from __future__ import annotations

import re
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
SKILLS = REPOSITORY / "skills"
ALLOWED_FRONTMATTER = {"name", "description", "license", "compatibility", "metadata"}
EMPHATIC = re.compile(r"\b(MUST|NEVER|ALWAYS|IMPORTANT|CRITICAL|REQUIRED)\b")
BANNED_PHRASES = ("show your reasoning", "think step by step", "double-check", "double check")


def split_skill(skill_dir: Path) -> tuple[str, str]:
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    _, frontmatter, body = text.split("---\n", 2)
    return frontmatter, body


def top_level_fields(frontmatter: str) -> dict[str, str]:
    return {m.group(1): m.group(2).strip() for m in re.finditer(r"^([A-Za-z][\w-]*):(.*)$", frontmatter, re.M)}


def words(text: str) -> int:
    return len(text.split())


def skill_texts(skill_dir: Path) -> list[Path]:
    return [skill_dir / "SKILL.md", *sorted((skill_dir / "references").glob("*.md"))]
