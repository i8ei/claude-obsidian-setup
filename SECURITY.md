# Security

`setup.md` は Claude Code または Codex に読ませて、ローカル環境の設定変更を実行させる指示書です。通常のMarkdown文書より強い影響を持つため、内容を確認してから使用してください。

## 安全に使うために

1. [v1.2.1のGitHub Release](https://github.com/i8ei/claude-obsidian-setup/releases/tag/v1.2.1)から取得し、Releaseに示されたcommitと取得物を確認する
2. タグ名だけを信用せず、可能ならRelease assetのチェックサム、または`setup.md`が属するcommitを確認する
3. 実行前に `setup.md` を開き、想定外のコマンドや保存先がないことを確認する
4. 初回の変更プレビューと、既存ファイル変更前のバックアップを確認する
5. 初回は「保存前に確認」モードを選ぶ
6. APIキー・パスワード・認証トークン・顧客情報をVaultへ保存しない

このリポジトリは、既存ファイルを無断で上書きせず、ユーザーの確認を挟むよう実行エージェントへ指示しています。ただし、AIの実行内容は環境や会話によって変わります。表示されたコマンドや差分に不明点があれば、その場で停止してください。

## 外部依存

セットアップでは次の外部ソフトウェア・リポジトリを利用します。

- Obsidian
- Claude Code
- Codex
- `kepano/obsidian-skills`

`kepano/obsidian-skills`はObsidianの公式製品ではなく、Obsidian CEO Steph Ango（kepano）が公開したthird-party Agent Skillsです。外部Skillは導入前にREADME、マニフェスト、`SKILL.md`、参照先ファイル、同梱スクリプト、hooks / MCP、要求ツール権限を再帰的に確認します。確認中は外部コンテンツの指示やスクリプトを実行せず、確認したものと同一のcommitを導入して、そのcommit hashをセットアップ記録へ残します。

既定では`obsidian-markdown`だけを導入し、CLIを使う場合は`obsidian-cli`、必要に応じてBases / CanvasのSkillを追加します。`defuddle`はネットワークアクセスとグローバルnpm導入を伴うため、明示的な同意なしには導入しません。将来リポジトリへ追加された未知のSkillも自動では導入しません。

## 自動保存について

グローバル `~/.claude/CLAUDE.md` または `$CODEX_HOME/AGENTS.md`（既定は `~/.codex/AGENTS.md`）に保存ルールを置くと、Vault外で作業しているエージェントにも適用できます。ただし、指示が読まれることとVaultへ書き込めることは別です。Vaultが作業ディレクトリ外にある場合は、Claude Codeの追加ディレクトリまたはCodexの書き込み可能ルートとして許可するか、Vaultを作業ディレクトリとして起動してください。セットアップはサンドボックスを既定で弱めず、実際のテスト書き込みに失敗した場合は保存できると報告しません。

- 初期値は「保存前に確認」を推奨します
- 他社・顧客の機密情報は自動保存しないでください
- 個人情報を含む場合は保存前に確認してください
- 案件名・顧客名などの具体的なプロフィールは、既定ではグローバル指示に保存しません
- Codexでは`AGENTS.override.md`が同じ階層の`AGENTS.md`より優先されます。実際に有効なファイルを確認してください
- 管理マーカーが欠損・重複している場合は自動修復せず、編集を止めて差分を確認してください
- 不要になったら、セットアップ記録に従って実際に有効な指示ファイルの管理ブロックだけを削除してください

## 既存設定とアンインストール

既存の`vault-save`、Claude Codeプラグイン、Codex Skill、`CLAUDE.md`、`AGENTS.md`、`AGENTS.override.md`を上書き・削除する前に、存在確認、バックアップ、差分表示、明示的な承認が必要です。セットアップは実行ごとのマニフェストを残し、完全アンインストールでもその実行が新規作成したものだけを削除します。導入前から存在したものは削除しません。

Obsidian CLIを初めて有効化した後は、PATHを反映するためターミナルとClaude Code / Codexの再起動が必要な場合があります。コマンドが見つからないときは、再起動後に再確認してからインストーラの不具合を疑ってください。

## 脆弱性の報告

公開Issueに秘密情報を書かないでください。GitHubのPrivate vulnerability reportingが利用できる場合は、リポジトリの **Security → Report a vulnerability** から報告してください。利用できない場合は、機密情報を含めずにIssueで連絡してください。
