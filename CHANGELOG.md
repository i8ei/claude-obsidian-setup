# Changelog

このプロジェクトの主な変更を記録します。

## [1.2.0] - 2026-07-23

### Added

- Codex向けの `AGENTS.md`、グローバル指示、`$vault-save` セットアップ
- Claude Codeのみ / Codexのみ / 両方から選べるセットアップ対象
- Codexの暗黙呼び出しを無効にする `agents/openai.yaml`

### Changed

- `setup.md` を実行エージェント判定型の共通指示書へ変更
- 手作りするCodex個人スキルを `~/.agents/skills`、組み込みインストーラ経由のスキルを `$CODEX_HOME/skills` として区別
- README・安全性・検証・アンインストール手順を両エージェント対応へ更新

## [1.1.0] - 2026-07-23

### Added

- 成果の保存モード（自動 / 保存前に確認 / 明示実行のみ）
- APIキー・顧客情報・個人情報を自動保存しない安全ルール
- `CLAUDE.md` 変更前のバックアップと管理コメント
- 再実行時の二重追記防止
- アンインストール・復旧手順
- Codex向け `AGENTS.md` オプション
- macOS / Windows別のダウンロード手順
- `SECURITY.md`
- GitHub ActionsによるMarkdown・リンク・プレースホルダー検査

### Changed

- `/vault-save` を旧custom commandからClaude Code Skillへ移行
- Obsidian Skillsを手動コピーからClaude Codeプラグイン導入へ変更
- `main`直取得ではなくReleaseタグ固定URLを推奨
- 動作確認環境とバージョン情報をsetup.md冒頭へ集約
- 完了報告に変更ファイル、バックアップ、保存モードを追加

## [1.0.0] - 2026-07-22

- Claude Code × Obsidianの対話式セットアップ指示書を公開
- Vaultルーティング表、`/vault-save`、グローバル保存ルールを導入
