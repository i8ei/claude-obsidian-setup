# claude-obsidian-setup

Claude Code に読ませるだけで、Obsidian との連携を自動セットアップしてくれる指示書です。

Obsidian のインストールから、AI が迷子にならないための Vault 設定（CLAUDE.md）、会話の成果を自動でノートに記録する仕組みまで、Claude Code が対話しながら進めてくれます。macOS / Windows 対応。実運用中の構成から汎用部分を抜き出したものです。

## 前提

- [Claude Code](https://claude.com/claude-code) がインストール済みでログインできること
- 所要時間: 30分くらい

## 使い方

1. [setup.md](setup.md) をダウンロードする

   ```bash
   curl -LO https://raw.githubusercontent.com/i8ei/claude-obsidian-setup/main/setup.md
   ```

2. ターミナルで Claude Code を起動して、こう頼む:

   > setup.md を読んで、書いてある通りにセットアップを進めて

3. あとは Claude の案内に従うだけ。アプリの画面操作（クリック）が必要な箇所だけ手を動かします

## 何が設定されるか

| 項目 | 内容 |
|---|---|
| Obsidian 本体 | 未導入なら brew / winget でインストール |
| Obsidian CLI | Claude がターミナルから Obsidian を検索・操作できる公式CLI |
| Vault 直下の CLAUDE.md | フォルダ×用途のルーティング表＋保存規約。AI用の地図 |
| グローバル CLAUDE.md | あなたのプロフィール＋「成果が出たら自動で Vault に記録する」ルール |
| /vault-save コマンド | 会話の成果を規約どおりに保存するスラッシュコマンド |
| 公式 Obsidian スキル | [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills)（Obsidian CEO 公開） |

最初のヒアリング（仕事内容・いま動いている案件・Claude に期待すること）への答えがそのままフォルダ構成と設定に反映されるので、出来上がりは人それぞれです。

## 運用の3原則（セットアップ後に Claude が説明してくれます）

1. **description は AI の目次** — 全ノートの frontmatter に1行要約を付ける（AIが書くので手間ゼロ）
2. **リンクのないノートは存在しないのと同じ** — 保存＝MOCへの1行＋関連ノートへの wikilink までワンセット
3. **［要確認］印は未来の自分への保険** — AI が書いた未確認情報に印を付け、後日「事実」として引用される事故を防ぐ

## License

MIT
