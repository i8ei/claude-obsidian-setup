"""Scenario tests for the kura-index add-on."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unicodedata
import unittest


KURA = Path(__file__).resolve().parents[1] / "addons" / "kura-index" / "kura.py"


class KuraIndexScenarioTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.vault = root / "Vault"
        self.db = root / "index" / "kura.db"
        notes = {
            "Projects/予算MOC.md": "---\ndescription: 予算の入口\n---\n[[令和8年度予算]]\n",
            "Projects/令和8年度予算.md": (
                "---\ndescription: 当初予算の分析\nlifecycle: active\n---\n"
                "一般会計の総額を整理した。[[存在しないノート]]\n"
            ),
            "Projects/旧予算メモ.md": (
                "---\ndescription: 旧稿\nlifecycle: superseded\n"
                "superseded_by: \"[[令和8年度予算]]\"\n---\n一般会計の古い数字\n"
            ),
            "Private/内部メモ.md": (
                "---\ndescription: 内部\nvisibility: internal\n---\n一般会計の内部検討\n"
            ),
            "Templates/テンプレート.md": "一般会計テンプレート\n",
            "CLAUDE.md": "一般会計 instructions\n",
            "inbox/説明なし.md": "医療の話\n",
            ".obsidian/hidden.md": "一般会計 hidden\n",
        }
        for rel, text in notes.items():
            path = self.vault / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        # macOS stores dakuten filenames as NFD; links in bodies are NFC
        nfd_name = unicodedata.normalize("NFD", "データベース") + ".md"
        (self.vault / "inbox" / nfd_name).write_text(
            "---\ndescription: 濁点ファイル\n---\n[[予算MOC]]\n", encoding="utf-8"
        )
        (self.vault / "inbox" / "リンク元.md").write_text(
            "---\ndescription: NFCリンク\n---\n[[データベース]]\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_kura(self, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
        base = {k: v for k, v in os.environ.items() if not k.startswith("KURA_")}
        full_env = {**base, "PYTHONIOENCODING": "utf-8", **(env or {})}
        return subprocess.run(
            [sys.executable, str(KURA), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=full_env,
        )

    def kura(self, *args: str) -> str:
        result = self.run_kura("--vault", str(self.vault), "--db", str(self.db), *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_missing_vault_config_fails_with_guidance(self) -> None:
        env = {k: v for k, v in os.environ.items() if not k.startswith("KURA_")}
        result = subprocess.run(
            [sys.executable, str(KURA), "search", "x"],
            capture_output=True, text=True, encoding="utf-8", env=env,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("KURA_VAULT", result.stderr)

    def test_environment_variables_configure_paths(self) -> None:
        result = self.run_kura(
            "build", env={"KURA_VAULT": str(self.vault), "KURA_DB": str(self.db)}
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.db.exists())

    def test_search_hides_retired_internal_and_non_notes(self) -> None:
        self.kura("build")
        hits = self.kura("search", "一般会計")
        self.assertIn("Projects/令和8年度予算.md", hits)
        self.assertNotIn("旧予算メモ", hits)
        self.assertNotIn("内部メモ", hits)
        self.assertNotIn("Templates", hits)
        self.assertNotIn("CLAUDE.md", hits)
        self.assertNotIn("hidden", hits)

        widened = self.kura("search", "一般会計", "--all")
        self.assertIn("旧予算メモ", widened)
        self.assertIn("内部メモ", widened)

    def test_two_character_terms_fall_back_to_like(self) -> None:
        self.kura("build")
        self.assertIn("inbox/説明なし.md", self.kura("search", "医療"))

    def test_nfd_filenames_resolve_nfc_links(self) -> None:
        self.kura("build")
        self.assertIn("inbox/リンク元.md", self.kura("backlinks", "データベース"))

    def test_check_reports_broken_links_and_missing_description(self) -> None:
        self.kura("build")
        report = self.kura("check")
        self.assertIn("[[存在しないノート]]", report)
        self.assertIn("inbox/説明なし.md", report)
        self.assertIn("## invalid superseded_by: 0", report)

    def test_memory_dir_is_search_only(self) -> None:
        memory = Path(self.tmp.name) / "memory"
        memory.mkdir()
        (memory / "feedback.md").write_text("一般会計の記憶\n", encoding="utf-8")
        self.kura("--memory-dir", str(memory), "build")
        self.assertNotIn("memory/", self.kura("search", "一般会計"))
        self.assertIn("memory/feedback.md", self.kura("search", "一般会計", "--scope", "all"))
        self.assertNotIn("memory/", self.kura("map"))

    def test_build_refuses_to_replace_index_when_vault_empties(self) -> None:
        self.kura("build")
        empty = Path(self.tmp.name) / "Empty"
        empty.mkdir()
        result = self.run_kura("--vault", str(empty), "--db", str(self.db), "build")
        self.assertEqual(result.returncode, 1)
        self.assertIn("ABORTED", result.stderr)
        self.assertIn("令和8年度予算", self.kura("search", "一般会計"))


if __name__ == "__main__":
    unittest.main()
