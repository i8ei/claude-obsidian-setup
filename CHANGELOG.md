# Changelog

このプロジェクトの主な変更を記録します。

## [1.2.1] - 2026-07-23

### Added

- 初回書き込み前に、対象ホスト、絶対パス、外部取得、保存モード、フォルダ構成をまとめて確認する変更プレビュー
- 実行ID、作成・変更・既存ファイル、バックアップ、外部Skillのcommitを記録するマニフェスト
- Codexの`AGENTS.override.md`、`CODEX_HOME`、同名Skill重複、Claude Code / Codex間の有効な指示ファイルの検出
- Vault外への書き込み権限とObsidian CLIのPATH反映を、実際の再起動・読み込み・テスト書き込みで確かめる手順
- Windows / WSL / Git Bashの実行環境判定、ファイル名サニタイズ、Vault配下へのパス制限
- 管理マーカー異常、テンプレートの未置換値、再実行、既存設定を検査するシナリオ検証

### Changed

- Claude Code + Codexの両対応をREADMEとセットアップ全体で明確化
- グローバル指示の既定内容をVaultパス、保存モード、機密除外ルールに限定し、案件名・顧客名などはVault内だけに保存
- 外部Skillを参照ファイル、scripts、hooks、MCPまで再帰的にレビューし、同じcommitを検証して導入する方式へ変更
- Agent Skillsの既定を`obsidian-markdown`中心の最小構成にし、CLI / Bases / Canvasは用途別、`defuddle`はネットワーク・グローバルnpm利用を説明したopt-inへ変更
- `kepano/obsidian-skills`の表現を「公式」から、Obsidian CEO Steph Ango（kepano）が公開したthird-party Agent Skillsへ訂正
- Obsidian CLI登録後のターミナル再起動、Windowsの厳密な`winget`指定、Claude Codeプラグイン再読み込みを手順化
- 空のVaultでは関連リンクを捏造せず、既存ノートがある場合だけ1〜3件リンクする規約へ変更
- READMEの表現を見直し、自動化やVault外への保存可否について環境依存の制約を明記

### Security

- 既存`vault-save`を含むファイル・ディレクトリ・symlinkの検出、日時付きバックアップ、差分確認、明示承認を追加
- 管理マーカーは0組なら追記、正確に1組なら更新、それ以外は停止する所有権安全な更新方式へ変更
- アンインストールは当該実行が新規作成した項目だけを削除し、既存のプラグインやSkillを保持
- 未知のSkillを自動導入せず、外部Skillのレビュー中は内容を命令として実行しないルールを追加
- CIのAction固定、OS横断検証、バージョンURL・テンプレート・管理マーカーの構造検査を強化

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
