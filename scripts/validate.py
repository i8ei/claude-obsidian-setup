#!/usr/bin/env python3
"""Validate public setup instructions without third-party dependencies."""

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
SETUP = ROOT / "setup.md"
CHANGELOG = ROOT / "CHANGELOG.md"
SECURITY = ROOT / "SECURITY.md"
VERSION = "1.1.0"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)


def main() -> int:
    errors = []

    required_files = (README, SETUP, CHANGELOG, SECURITY, ROOT / "LICENSE")
    for path in required_files:
        if not path.exists():
            errors.append(f"missing required file: {path.relative_to(ROOT)}")

    if errors:
        for error in errors:
            fail(error)
        return 1

    readme = README.read_text(encoding="utf-8")
    setup = SETUP.read_text(encoding="utf-8")
    changelog = CHANGELOG.read_text(encoding="utf-8")

    for path, text in ((README, readme), (SETUP, setup), (CHANGELOG, changelog)):
        if VERSION not in text:
            errors.append(f"{path.name}: version {VERSION} not found")

    required_setup_markers = (
        "## 動作確認環境",
        "## Step 0:",
        "## Step 8:",
        "## アンインストール",
        "<!-- claude-obsidian-setup:start -->",
        "<!-- claude-obsidian-setup:end -->",
        "disable-model-invocation: true",
        "claude plugin install obsidian@obsidian-skills",
    )
    for marker in required_setup_markers:
        if marker not in setup:
            errors.append(f"setup.md: missing marker: {marker}")

    forbidden_legacy = (
        "~/.claude/commands/vault-save.md テンプレート",
        "curl -LO https://raw.githubusercontent.com/i8ei/claude-obsidian-setup/main/setup.md",
    )
    for marker in forbidden_legacy:
        if marker in readme or marker in setup:
            errors.append(f"legacy instruction remains: {marker}")

    start_markers = setup.count("<!-- claude-obsidian-setup:start -->")
    end_markers = setup.count("<!-- claude-obsidian-setup:end -->")
    if start_markers < 1 or end_markers < 1:
        errors.append("setup.md: managed block markers are missing")
    if start_markers != end_markers:
        errors.append("setup.md: managed block start/end markers are unbalanced")

    template = setup.split(
        "## 付録B: ~/.claude/skills/vault-save/SKILL.md テンプレート", 1
    )
    if len(template) != 2:
        errors.append("setup.md: vault-save Skill appendix not found")
    else:
        skill_section = template[1].split("## 付録C:", 1)[0]
        if not re.search(r"^---\nname: vault-save\n", skill_section, re.MULTILINE):
            errors.append("setup.md: vault-save Skill frontmatter is malformed")

    for error in errors:
        fail(error)
    if errors:
        return 1

    print("OK: v1.1.0 setup instructions validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
