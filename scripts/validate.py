#!/usr/bin/env python3
"""Validate the published setup guide without third-party dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
SETUP = ROOT / "setup.md"
CHANGELOG = ROOT / "CHANGELOG.md"
SECURITY = ROOT / "SECURITY.md"
VERSION_FILE = ROOT / "VERSION"

VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
PINNED_OBSIDIAN_SKILLS_COMMIT = "a1dc48e68138490d522c04cbf5822214c6eb1202"
RAW_SETUP_URL_PATTERN = re.compile(
    r"https://raw\.githubusercontent\.com/i8ei/claude-obsidian-setup/"
    r"v(?P<version>\d+\.\d+\.\d+)/setup\.md"
)
PLACEHOLDER_PATTERN = re.compile(r"〈[^〉\n]+〉")
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


@dataclass(frozen=True)
class ManagedBlock:
    """Describe the marker state of one managed instruction block."""

    state: str
    start: int | None = None
    end: int | None = None


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)


def inspect_managed_block(text: str, name: str) -> ManagedBlock:
    """Classify a managed block as fresh, existing, or malformed."""

    start_marker = f"<!-- {name}:start -->"
    end_marker = f"<!-- {name}:end -->"
    starts = [match.start() for match in re.finditer(re.escape(start_marker), text)]
    ends = [match.end() for match in re.finditer(re.escape(end_marker), text)]

    if not starts and not ends:
        return ManagedBlock("fresh")
    if len(starts) == len(ends) == 1 and starts[0] < ends[0]:
        return ManagedBlock("existing", starts[0], ends[0])
    return ManagedBlock("malformed")


def replace_managed_block(text: str, name: str, replacement: str) -> str:
    """Append or replace exactly one managed block; reject ambiguous input."""

    state = inspect_managed_block(text, name)
    if state.state == "malformed":
        raise ValueError(f"malformed managed block: {name}")
    if state.state == "fresh":
        if not text:
            prefix = ""
        elif text.endswith("\n\n"):
            prefix = text
        elif text.endswith("\n"):
            prefix = f"{text}\n"
        else:
            prefix = f"{text}\n\n"
        return f"{prefix}{replacement.rstrip()}\n"
    assert state.start is not None and state.end is not None
    return f"{text[:state.start]}{replacement.rstrip()}{text[state.end:]}"


def select_codex_instruction_file(existing_paths: set[str], codex_home: str) -> str:
    """Return the effective Codex global instruction file."""

    base = codex_home.rstrip("/\\")
    override = f"{base}/AGENTS.override.md"
    standard = f"{base}/AGENTS.md"
    return override if override in existing_paths else standard


def is_safe_windows_relative_path(candidate: str) -> bool:
    """Reject absolute, traversal, or Windows-invalid Vault-relative paths."""

    if not candidate or candidate.startswith(("/", "\\")):
        return False
    path = PureWindowsPath(candidate)
    if path.is_absolute() or path.drive:
        return False

    parts = re.split(r"[\\/]", candidate)
    for part in parts:
        if not part or part in {".", ".."}:
            return False
        if re.search(r"[\x00-\x1f<>:\"|?*]", part) or part.endswith((" ", ".")):
            return False
        stem = part.split(".", 1)[0].rstrip(" .").upper()
        if stem in WINDOWS_RESERVED_NAMES:
            return False
    return True


def require_any(text: str, alternatives: tuple[str, ...], label: str) -> str | None:
    """Return an error when none of the required alternatives is present."""

    if any(item in text for item in alternatives):
        return None
    return f"setup.md: missing {label} ({' / '.join(alternatives)})"


def validate() -> list[str]:
    errors: list[str] = []
    required_files = (
        README,
        SETUP,
        CHANGELOG,
        SECURITY,
        VERSION_FILE,
        ROOT / "LICENSE",
    )
    for path in required_files:
        if not path.is_file():
            errors.append(f"missing required file: {path.relative_to(ROOT)}")

    if errors:
        return errors

    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not VERSION_PATTERN.fullmatch(version):
        errors.append("VERSION: expected MAJOR.MINOR.PATCH")

    documents = {
        "README.md": README.read_text(encoding="utf-8"),
        "setup.md": SETUP.read_text(encoding="utf-8"),
        "CHANGELOG.md": CHANGELOG.read_text(encoding="utf-8"),
        "SECURITY.md": SECURITY.read_text(encoding="utf-8"),
    }
    for name, text in documents.items():
        if version not in text:
            errors.append(f"{name}: version {version} not found")

    readme = documents["README.md"]
    setup = documents["setup.md"]
    changelog = documents["CHANGELOG.md"]
    security = documents["SECURITY.md"]

    for name in ("README.md", "setup.md", "SECURITY.md"):
        if PINNED_OBSIDIAN_SKILLS_COMMIT not in documents[name]:
            errors.append(
                f"{name}: pinned obsidian-skills commit is missing or mismatched"
            )

    raw_versions = {
        match.group("version") for match in RAW_SETUP_URL_PATTERN.finditer(readme)
    }
    if raw_versions != {version}:
        errors.append(
            "README.md: versioned setup URLs must all match VERSION "
            f"(found: {sorted(raw_versions)})"
        )
    if f"## [{version}]" not in changelog:
        errors.append(f"CHANGELOG.md: missing release heading [{version}]")

    required_setup_strings = (
        "## 動作確認環境",
        "## Step 0:",
        "## アンインストール",
        "disable-model-invocation: true",
        "allow_implicit_invocation: false",
        "AGENTS.override.md",
        "$CODEX_HOME",
        "$vault-save",
        "claude plugin install obsidian@obsidian-skills",
        "/reload-plugins",
        "@AGENTS.md",
        "--add-dir",
        "--ref",
        "winget list --id Obsidian.Obsidian -e",
        "exec --ephemeral --skip-git-repo-check",
        "〈保存モード文〉",
    )
    for required in required_setup_strings:
        if required not in setup:
            errors.append(f"setup.md: missing required content: {required}")

    requirement_groups = (
        (("run ID", "run_id", "実行ID"), "per-run ownership record"),
        (("created_by_this_run",), "ownership-safe uninstall flag"),
        (("command -v obsidian",), "POSIX Obsidian CLI PATH check"),
        (("Get-Command obsidian",), "PowerShell Obsidian CLI PATH check"),
        (("WSL", "Git Bash"), "Windows host detection"),
        (("予約名", "reserved"), "Windows reserved-name validation"),
        (("0組", "0 組"), "zero managed-marker policy"),
        (("1組", "1 組"), "single managed-marker policy"),
        (("不正", "malformed", "中止して診断"), "malformed-marker policy"),
        (("同じコミット", "同一コミット", "same commit"), "review/install pinning"),
        (("書き込み可能", "writable root", "writable_roots"), "sandbox write scope"),
        (("既存ノートがなければ", "関連ノートがなければ"), "empty Vault link rule"),
        (("Vault配下", "Vault の配下"), "resolved Vault path containment"),
    )
    for alternatives, label in requirement_groups:
        error = require_any(setup, alternatives, label)
        if error:
            errors.append(error)

    managed_names = ("claude-obsidian-setup", "codex-obsidian-setup")
    for name in managed_names:
        starts = setup.count(f"<!-- {name}:start -->")
        ends = setup.count(f"<!-- {name}:end -->")
        if starts < 1 or starts != ends:
            errors.append(
                f"setup.md: {name} example markers must be present and balanced "
                f"(start={starts}, end={ends})"
            )

    old_mode_placeholder = "〈下記3モードのうち選んだ1行〉"
    if old_mode_placeholder in setup:
        errors.append(
            f"setup.md: obsolete placeholder remains: {old_mode_placeholder}"
        )

    placeholders = set(PLACEHOLDER_PATTERN.findall(setup))
    if "〈保存モード文〉" not in placeholders:
        errors.append("setup.md: canonical save-mode placeholder is missing")
    if "/path/to/YourVault/" not in setup:
        errors.append("setup.md: Vault path replacement token is missing")
    if not re.search(
        r"(プレースホルダー|置き換え)[^\n]{0,100}(残っていない|0件)", setup
    ):
        errors.append("setup.md: generated-artifact placeholder check is missing")

    appendix_pairs = (
        (
            "## 付録B-1: Claude Code用 vault-save テンプレート",
            "## 付録B-2:",
            "Claude Code",
        ),
        (
            "## 付録B-2: Codex用 vault-save テンプレート",
            "## 付録C:",
            "Codex",
        ),
    )
    for start_heading, end_heading, label in appendix_pairs:
        split = setup.split(start_heading, 1)
        if len(split) != 2:
            errors.append(f"setup.md: {label} vault-save appendix not found")
            continue
        skill_section = split[1].split(end_heading, 1)[0]
        if not re.search(r"^---\nname: vault-save\n", skill_section, re.MULTILINE):
            errors.append(f"setup.md: {label} vault-save frontmatter is malformed")

    forbidden_strings = (
        "curl -LO https://raw.githubusercontent.com/i8ei/claude-obsidian-setup/main/setup.md",
        "official Obsidian skills",
        "公式のObsidianスキル",
        'codex --cd "<Vault絶対パス>" --ask-for-approval never '
        '"Summarize the current instructions without changing files."',
    )
    combined = "\n".join(documents.values())
    for forbidden in forbidden_strings:
        if forbidden in combined:
            errors.append(f"legacy or unsafe instruction remains: {forbidden}")
    if re.search(r"skills/<skill-name>`?\s*をすべてインストール", combined):
        errors.append("legacy or unsafe instruction remains: install every upstream Skill")

    if "GitHub Release" not in security or f"v{version}" not in security:
        errors.append("SECURITY.md: immutable version/release guidance is incomplete")

    return errors


def main() -> int:
    errors = validate()
    for error in errors:
        fail(error)
    if errors:
        return 1

    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    print(f"OK: v{version} setup instructions validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
