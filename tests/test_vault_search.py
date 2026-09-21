"""Scenario tests for the vault-search add-on."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unicodedata
import unittest


VAULT_SEARCH = (
    Path(__file__).resolve().parents[1] / "addons" / "vault-search" / "vault_search.py"
)


class VaultSearchScenarioTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.vault = root / "Vault"
        self.db = root / "index" / "vault_search.db"
        notes = {
            "Projects/予算MOC.md": "---\ndescription: 予算の入口\n---\n[[令和8年度予算]]\n",
            "Projects/令和8年度予算.md": (
                "---\ndescription: 当初予算の分析\nlifecycle: active\n---\n"
                "一般会計の総額を整理した。［要確認］金額の根拠を確認すること。[[存在しないノート]]\n"
            ),
            "Projects/旧予算メモ.md": (
                "---\ndescription: 旧稿\nlifecycle: superseded\n"
                "superseded_by: \"[[令和8年度予算]]\"\n---\n一般会計の古い数字\n"
            ),
            "Projects/未更新後継メモ.md": (
                "---\ndescription: 不整合メモ\nlifecycle: active\n"
                "superseded_by: \"[[令和8年度予算]]\"\n---\n後継があるのにactiveのまま\n"
            ),
            "Private/内部メモ.md": (
                "---\ndescription: 内部\nvisibility: internal\n---\n一般会計の内部検討\n"
            ),
            "Templates/テンプレート.md": "一般会計テンプレート\n",
            "CLAUDE.md": "一般会計 instructions\n",
            "inbox/説明なし.md": "医療の話。全角のＡＩ技術を活用。\n",
            "inbox/archive/昔の資料.md": "一般会計の原典アーカイブ\n",
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

    def run_tool(
        self, *args: str, env: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess:
        base = {
            k: v for k, v in os.environ.items()
            if not k.startswith("VAULT_SEARCH_") and not k.startswith("KURA_")
        }
        full_env = {**base, "PYTHONIOENCODING": "utf-8", **(env or {})}
        return subprocess.run(
            [sys.executable, str(VAULT_SEARCH), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=full_env,
        )

    def vault_search(self, *args: str) -> str:
        result = self.run_tool("--vault", str(self.vault), "--db", str(self.db), *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_missing_vault_config_fails_with_guidance(self) -> None:
        env = {
            k: v for k, v in os.environ.items()
            if not k.startswith("VAULT_SEARCH_") and not k.startswith("KURA_")
        }
        result = subprocess.run(
            [sys.executable, str(VAULT_SEARCH), "search", "x"],
            capture_output=True, text=True, encoding="utf-8", env=env,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("VAULT_SEARCH_VAULT", result.stderr)

    def test_environment_variables_configure_paths(self) -> None:
        result = self.run_tool(
            "build",
            env={
                "VAULT_SEARCH_VAULT": str(self.vault),
                "VAULT_SEARCH_DB": str(self.db),
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.db.exists())

    def test_backward_compatible_kura_env_vars(self) -> None:
        result = self.run_tool(
            "build",
            env={"KURA_VAULT": str(self.vault), "KURA_DB": str(self.db)},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.db.exists())

    def test_search_hides_retired_internal_and_non_notes(self) -> None:
        self.vault_search("build")
        hits = self.vault_search("search", "一般会計")
        self.assertIn("Projects/令和8年度予算.md", hits)
        self.assertNotIn("旧予算メモ", hits)
        self.assertNotIn("内部メモ", hits)
        self.assertNotIn("Templates", hits)
        self.assertNotIn("CLAUDE.md", hits)
        self.assertNotIn("hidden", hits)
        self.assertNotIn("inbox/archive", hits)  # inbox/archive/ is hidden by default

        widened = self.vault_search("search", "一般会計", "--all")
        self.assertIn("旧予算メモ", widened)
        self.assertIn("内部メモ", widened)
        self.assertIn("inbox/archive/昔の資料.md", widened)

    def test_two_character_terms_fall_back_to_like(self) -> None:
        self.vault_search("build")
        self.assertIn("inbox/説明なし.md", self.vault_search("search", "医療"))

    def test_nfkc_normalization_matches_fullwidth_and_halfwidth(self) -> None:
        self.vault_search("build")
        # Text has fullwidth 'ＡＩ', query uses halfwidth 'AI'
        hits = self.vault_search("search", "AI")
        self.assertIn("inbox/説明なし.md", hits)

    def test_nfd_filenames_resolve_nfc_links(self) -> None:
        self.vault_search("build")
        self.assertIn(
            "inbox/リンク元.md", self.vault_search("backlinks", "データベース")
        )

    def test_check_reports_broken_links_missing_desc_and_unverified(self) -> None:
        self.vault_search("build")
        report = self.vault_search("check")
        self.assertIn("[[存在しないノート]]", report)
        self.assertIn("inbox/説明なし.md", report)
        self.assertIn("## invalid superseded_by: 0", report)
        # Check unverified marker report
        self.assertIn("## unverified markers ([要確認]): 1", report)
        self.assertIn("Projects/令和8年度予算.md", report)
        # Check lifecycle mismatch report
        self.assertIn(
            "## superseded_by set but lifecycle not superseded: 1", report
        )
        self.assertIn("Projects/未更新後継メモ.md", report)

    def test_stale_warning_when_vault_changes(self) -> None:
        self.vault_search("build")
        # Add a new note to make index stale
        time.sleep(0.01)
        (self.vault / "inbox" / "新規追加.md").write_text("新規ノート内容\n", encoding="utf-8")
        result = self.run_tool(
            "--vault", str(self.vault), "--db", str(self.db), "search", "新規"
        )
        self.assertIn("WARNING: index is stale", result.stderr)

    def test_scan_command_outputs_inventory(self) -> None:
        result = self.run_tool(
            "--vault", str(self.vault), "--db", str(self.db), "scan", str(self.vault / "Projects")
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Import Inventory:", result.stdout)
        self.assertIn("Total:", result.stdout)
        self.assertIn("Format breakdown", result.stdout)

    def test_memory_dir_is_search_only(self) -> None:
        memory = Path(self.tmp.name) / "memory"
        memory.mkdir()
        (memory / "feedback.md").write_text("一般会計の記憶\n", encoding="utf-8")
        self.vault_search("--memory-dir", str(memory), "build")
        self.assertNotIn("memory/", self.vault_search("search", "一般会計"))
        self.assertIn(
            "memory/feedback.md",
            self.vault_search("search", "一般会計", "--scope", "all"),
        )
        self.assertNotIn("memory/", self.vault_search("map"))

    def test_build_refuses_to_replace_index_when_vault_empties(self) -> None:
        self.vault_search("build")
        empty = Path(self.tmp.name) / "Empty"
        empty.mkdir()
        result = self.run_tool(
            "--vault", str(empty), "--db", str(self.db), "build"
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("ABORTED", result.stderr)
        self.assertIn("令和8年度予算", self.vault_search("search", "一般会計"))


if __name__ == "__main__":
    unittest.main()
