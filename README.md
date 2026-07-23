# claude-obsidian-setup

Claude Code または Codex に読ませるだけで、Obsidian との連携を自動セットアップしてくれる指示書です。

Obsidian のインストールから、AI が迷子にならないための Vault 設定（`CLAUDE.md` / `AGENTS.md`）、会話の成果をノートに記録する仕組みまで、実行中のエージェントが対話しながら進めてくれます。実運用中の構成から汎用部分を抜き出したものです。

- **最終更新**: 2026-07（v1.2.0）
- **対応**: macOS / Windows（Linux は実験的）
- **必要環境**: [Claude Code](https://claude.com/claude-code) または [Codex](https://developers.openai.com/codex/)、Obsidian（インストーラ **1.12.7 以上**）
- 対応バージョンの詳細は [setup.md](setup.md) 冒頭の「動作確認環境」を参照

## 前提

- Claude Code または Codex がインストール済みでログインできること
- 所要時間: 30分くらい

## 使い方

1. [setup.md](setup.md) をダウンロードする（バージョン固定を推奨）

   **macOS / Linux**

   ```bash
   curl -fLO https://raw.githubusercontent.com/i8ei/claude-obsidian-setup/v1.2.0/setup.md
   ```

   **Windows (PowerShell)**

   ```powershell
   Invoke-WebRequest -Uri "https://raw.githubusercontent.com/i8ei/claude-obsidian-setup/v1.2.0/setup.md" -OutFile "setup.md"
   ```

   > **実行前に一度目を通してください。** setup.md はAIエージェントに実行させる指示書です。何をするファイルか自分の目で確認してから使うのが安全です（[SECURITY.md](SECURITY.md)）。

2. ターミナルで使いたいエージェントを起動する:

   ```bash
   claude
   # or
   codex
   ```

3. こう頼む:

   > setup.md を読んで、書いてある通りにセットアップを進めて

4. あとは案内に従うだけ。アプリの画面操作（クリック）が必要な箇所だけ手を動かします

## 何が設定されるか

| 項目 | 内容 |
|---|---|
| Obsidian 本体 | 未導入なら brew / winget でインストール |
| Obsidian CLI | エージェントがターミナルから Obsidian を検索・操作できる公式CLI（インストーラ 1.12.7 以上が必要） |
| Vault 直下のAIガイド | Claude Codeは `CLAUDE.md`、Codexは `AGENTS.md`。フォルダ×用途のルーティング表＋保存規約 |
| グローバル指示 | `~/.claude/CLAUDE.md` / `$CODEX_HOME/AGENTS.md`（既定は `~/.codex/AGENTS.md`）にプロフィールと保存モードを追記 |
| vault-save スキル | Claude Codeは `/vault-save`、Codexは `$vault-save` で成果を規約どおりに保存 |
| 公式 Obsidian スキル | [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills)（Obsidian CEO 公開）を各エージェントの方式で導入 |

最初のヒアリング（仕事内容・いま動いている案件・AIに期待すること・保存モード）への答えがそのままフォルダ構成と設定に反映されるので、出来上がりは人それぞれです。

## 運用の3原則（セットアップ後にエージェントが説明します）

1. **description は AI の目次** — 全ノートの frontmatter に1行要約を付ける（AIが書くので手間ゼロ）
2. **リンクのないノートは存在しないのと同じ** — 保存＝MOCへの1行＋関連ノートへの wikilink までワンセット
3. **［要確認］印は未来の自分への保険** — AI が書いた未確認情報に印を付け、後日「事実」として引用される事故を防ぐ

## 安全性

- 自動保存は **セットアップ時にモードを選べます**（自動 / 保存前に確認 / 明示呼び出しのみ）。初期値は「保存前に確認」を推奨
- APIキー・パスワード・他社案件などの機密情報は自動保存しない既定ルールが入ります
- 詳しくは [SECURITY.md](SECURITY.md)

## アンインストール

セットアップ完了時に、作成・変更したファイルの一覧とアンインストール手順が表示されます。対象エージェントのグローバル指示に追加された管理ブロックだけを削除すれば、Vaultへの保存ルールは止まります。

## 変更履歴

[CHANGELOG.md](CHANGELOG.md) を参照。

## License

MIT
