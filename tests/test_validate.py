"""Scenario tests for setup validation helpers."""

from __future__ import annotations

import unittest

from scripts.validate import (
    inspect_managed_block,
    is_safe_windows_relative_path,
    replace_managed_block,
    select_codex_instruction_file,
)


NAME = "codex-obsidian-setup"
BLOCK = (
    "<!-- codex-obsidian-setup:start -->\n"
    "Vault instructions\n"
    "<!-- codex-obsidian-setup:end -->"
)


class ManagedBlockScenarioTests(unittest.TestCase):
    def test_fresh_install_appends_one_managed_block(self) -> None:
        original = "User content with intentional spaces  \n"

        updated = replace_managed_block(original, NAME, BLOCK)

        self.assertEqual(inspect_managed_block(updated, NAME).state, "existing")
        self.assertTrue(updated.startswith(original))

    def test_existing_install_replaces_only_managed_block(self) -> None:
        original = f"Before\n{BLOCK}\nAfter\n"
        replacement = BLOCK.replace("Vault instructions", "Updated instructions")

        updated = replace_managed_block(original, NAME, replacement)

        self.assertIn("Before", updated)
        self.assertIn("After", updated)
        self.assertIn("Updated instructions", updated)
        self.assertNotIn("\nVault instructions\n", updated)

    def test_rerun_is_idempotent(self) -> None:
        first = replace_managed_block("User content\n", NAME, BLOCK)
        second = replace_managed_block(first, NAME, BLOCK)

        self.assertEqual(second, first)
        self.assertEqual(second.count(f"<!-- {NAME}:start -->"), 1)

    def test_malformed_markers_stop_without_editing(self) -> None:
        malformed = f"{BLOCK}\n{BLOCK}\n"

        self.assertEqual(inspect_managed_block(malformed, NAME).state, "malformed")
        with self.assertRaises(ValueError):
            replace_managed_block(malformed, NAME, BLOCK)


class CodexOverrideScenarioTests(unittest.TestCase):
    def test_override_masks_standard_global_file(self) -> None:
        codex_home = "/Users/example/.codex"
        existing = {
            f"{codex_home}/AGENTS.md",
            f"{codex_home}/AGENTS.override.md",
        }

        selected = select_codex_instruction_file(existing, codex_home)

        self.assertEqual(selected, f"{codex_home}/AGENTS.override.md")

    def test_standard_file_is_used_without_override(self) -> None:
        codex_home = "/Users/example/.codex"

        selected = select_codex_instruction_file(set(), codex_home)

        self.assertEqual(selected, f"{codex_home}/AGENTS.md")


class WindowsPathScenarioTests(unittest.TestCase):
    def test_accepts_safe_vault_relative_path(self) -> None:
        self.assertTrue(is_safe_windows_relative_path("Projects\\Client A\\Note.md"))

    def test_rejects_absolute_and_traversal_paths(self) -> None:
        unsafe = (
            "C:\\Vault\\Note.md",
            "\\\\server\\share\\Note.md",
            "..\\Outside.md",
            "Folder/../Outside.md",
        )
        for candidate in unsafe:
            with self.subTest(candidate=candidate):
                self.assertFalse(is_safe_windows_relative_path(candidate))

    def test_rejects_reserved_or_invalid_windows_names(self) -> None:
        unsafe = (
            "CON.md",
            "Folder\\AUX",
            "Folder\\bad?.md",
            "Folder\\trailing. ",
            "Folder\\null\x00byte.md",
            "Folder\\tab\tname.md",
            "Folder\\unit\x1fseparator.md",
        )
        for candidate in unsafe:
            with self.subTest(candidate=candidate):
                self.assertFalse(is_safe_windows_relative_path(candidate))


if __name__ == "__main__":
    unittest.main()
