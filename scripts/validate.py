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
VERSION = "1.2.0"


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
        "<!-- codex-obsidian-setup:start -->",
        "<!-- codex-obsidian-setup:end -->",
        "disable-model-invocation: true",
        "allow_implicit_invocation: false",
        "~/.codex/AGENTS.md",
        "~/.agents/skills/vault-save/SKILL.md",
        "$vault-save",
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

    for managed_name in ("claude-obsidian-setup", "codex-obsidian-setup"):
        start_markers = setup.count(f"<!-- {managed_name}:start -->")
        end_markers = setup.count(f"<!-- {managed_name}:end -->")
        if start_markers < 1 or end_markers < 1:
            errors.append(f"setup.md: {managed_name} markers are missing")
        if start_markers != end_markers:
            errors.append(f"setup.md: {managed_name} markers are unbalanced")

    template = setup.split(
        "## 付録B-1: Claude Code用 vault-save テンプレート", 1
    )
    if len(template) != 2:
        errors.append("setup.md: Claude Code vault-save appendix not found")
    else:
        skill_section = template[1].split("## 付録B-2:", 1)[0]
        if not re.search(r"^---\nname: vault-save\n", skill_section, re.MULTILINE):
            errors.append("setup.md: Claude Code vault-save frontmatter is malformed")

    codex_template = setup.split(
        "## 付録B-2: Codex用 vault-save テンプレート", 1
    )
    if len(codex_template) != 2:
        errors.append("setup.md: Codex vault-save appendix not found")
    else:
        skill_section = codex_template[1].split("## 付録C:", 1)[0]
        if not re.search(r"^---\nname: vault-save\n", skill_section, re.MULTILINE):
            errors.append("setup.md: Codex vault-save frontmatter is malformed")
        if "allow_implicit_invocation: false" not in skill_section:
            errors.append("setup.md: Codex vault-save must disable implicit invocation")

    for error in errors:
        fail(error)
    if errors:
        return 1

    print("OK: v1.2.0 setup instructions validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
