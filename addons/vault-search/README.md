# vault-search: Vault の全文検索・点検エンジン（追加パッケージ）

Obsidian Vault のノートを SQLite の全文検索にかけ、AI エージェントが grep より速く（0秒）、正確にノートを探せるようにする追加パッケージです。

> **このファイルを受け取った方へ**: ターミナルで Claude Code または Codex を起動し、
> 「**`addons/vault-search/README.md` を読み、導入手順の通りに入れて**」と依頼してください。

## 何ができるか

| コマンド | 用途 |
|---|---|
| `search "<語>"` | 日本語の全文検索。スペース区切りは AND、`--any` で OR（0秒で完全一致・2文字対応） |
| `map` | 全ノートの「パス＋description」の一覧（AI 用の地図） |
| `links <ノート>` / `backlinks <ノート>` | リンクの出入り |
| `orphans` | どこからもリンクされていないノート |
| `check` | リンク切れ、［要確認］印の棚卸し、description 書き忘れ、frontmatter 誤り、重複タイトル |
| `scan <フォルダ>` | 取り込み前の棚卸し（読み取り専用）。形式の内訳、更新日範囲、版違い候補の一覧 |
| `build` | インデックスを作り直す |

設計の約束:

- **正本はノート**です。インデックスは使い捨ての派生物で、壊れたら `build` で作り直せます。ノートには一切書き込みません
- インデックスは **Vault の外**（macOS/Linux は `~/.local/share/vault-search/`、Windows は `%LOCALAPPDATA%\vault-search\`）に置きます。iCloud・Obsidian Sync・git にバイナリが混ざりません
- Vault の読み取りに失敗してノート数が半分以下に減った場合は、**既存のインデックスを置き換えずに中止**します（本当に大量削除したときだけ `build --force`）
- macOS の濁点ファイル名（NFD）とノート本文（NFC）の食い違いを正規化しています
- 全角英数・半角カナの表記ゆれを **NFKC 正規化** で吸収し、「ＡＩ」と「AI」が同じようにヒットします
- 2文字の語（「医療」「予算」など）は trigram 検索で拾えないため、自動で LIKE 検索に切り替えます
- インデックス作成後に Vault が更新された場合、検索時に `WARNING: index is stale` の警告を表示します（静かな陳腐化を防止）

## 検索を賢くする frontmatter（任意）

書かなくても動きます。書くと、古いノートが検索結果に混ざらなくなります。

```yaml
---
description: このノートの一行要約     # 必須規約（本体setupと同じ）
lifecycle: active                    # active / reference / raw / superseded / archive
visibility: internal                 # public / internal
superseded_by: "[[後継ノート]]"        # lifecycle: superseded のとき必須
orphan_status: intentional           # リンクされなくてよいノート
---
```

- 通常の `search` は `superseded`・`archive`・`internal`（および `inbox/archive/`）を**隠します**（消すのではありません）
- `--include-retired`（旧稿・原典も）、`--include-internal`（内部も）、`--all`（両方）で広げます
- **検索に出ないことは、存在しないことを意味しません**

## 動作要件

- Python 3.9 以上（追加ライブラリ不要）
- SQLite 3.34 以上（FTS5 trigram）。起動時に自動で確かめ、足りなければ理由を表示して止まります

---

**ここから下は Claude Code / Codex への指示です。** 本体 setup.md の「絶対に守る安全規則」を同様に守る。書き込み前に、下記 1〜5 で作る・変えるファイルの絶対パスをまとめて提示し、承認を得る。

## 導入手順

### 1. 事前確認（読み取りのみ）

1. `python3 --version`（Windows は `py --version`）が 3.9 以上か
2. `python3 -c "import sqlite3; c=sqlite3.connect(':memory:'); c.execute(\"create virtual table t using fts5(x, tokenize='trigram')\"); print(sqlite3.sqlite_version)"` が成功するか。失敗したら導入を止め、Python の更新（python.org 版または Homebrew 版）を案内する
3. Vault の絶対パスを、本体セットアップの run manifest か Vault 直下の `CLAUDE.md` / `AGENTS.md` から特定する。見つからなければユーザーに聞く

### 2. スクリプトの配置

- 置き場所: macOS/Linux は `~/.local/share/vault-search/vault_search.py`、Windows は `%LOCALAPPDATA%\vault-search\vault_search.py`
- 取得元は**タグで固定**する。ユーザーが使った本体と同じバージョンのタグを使い、`main` は使わない
- 配置後、中身を一度読んでからユーザーに要点を伝える

### 3. 初回ビルドと疎通確認

```bash
python3 ~/.local/share/vault-search/vault_search.py --vault "<Vaultの絶対パス>" build
python3 ~/.local/share/vault-search/vault_search.py --vault "<Vaultの絶対パス>" search "<Vault内に確実にある語>"
python3 ~/.local/share/vault-search/vault_search.py --vault "<Vaultの絶対パス>" check
```

`built: N notes` の N が、Vault 内の `.md` の数（`.obsidian` などの隠しフォルダ、`Templates`、`CLAUDE.md`、`AGENTS.md` を除く）とおおむね一致することを確かめる。`check` の結果は**報告のみ**とし、ノートの修正は別途ユーザーの指示を待つ。

`Templates` 以外にも索引から外したいフォルダがあれば `--exclude "Templates,Attachments"` で指定する（環境変数 `VAULT_SEARCH_EXCLUDE` でも可）。

### 4. エージェントへの使い方の登録

Vault 直下の AI ガイド（`CLAUDE.md` / `AGENTS.md`）に、本体と同じ管理ブロック方式で次を追記する。マーカー名は `vault-search`。

```markdown
<!-- vault-search:start -->
## ノートの探し方
Vault 内を探すときは grep / find より先に次を使う（`VAULT_SEARCH_VAULT` 設定済み）。
- `python3 ~/.local/share/vault-search/vault_search.py search "<語>" --k 10` — スペース区切りは AND
- `python3 ~/.local/share/vault-search/vault_search.py map` — 全ノートのパスと description
- 旧稿・原典・内部ノートも探すときは `--all`。検索に出ないことは、存在しないことを意味しない
- ノートを作成・更新・改名・削除した直後は `python3 ~/.local/share/vault-search/vault_search.py build`
<!-- vault-search:end -->
```

あわせて、シェルの設定（macOS は `~/.zshrc`、Windows はユーザー環境変数）に `VAULT_SEARCH_VAULT` を設定する。設定したら、**新しいシェルで** `search` が `--vault` なしで動くことを確かめる（後方互換として `KURA_VAULT` もサポート）。

Windows では例の `python3 ~/.local/share/vault-search/vault_search.py` を `py "$env:LOCALAPPDATA\vault-search\vault_search.py"` に読み替えて書く。

### 5. 自動再構築（任意・opt-in）

手動の `build` だけでも運用できます。ユーザーが望んだ場合のみ、1時間ごとの再構築を登録する。

- macOS: `~/Library/LaunchAgents/` に launchd の plist（`StartInterval` 3600、`EnvironmentVariables` に `VAULT_SEARCH_VAULT`）。登録後は `launchctl list | grep vault-search` で**実在を確かめる**
- Windows: タスクスケジューラに1時間ごとのタスク
- Linux: `crontab` か systemd user timer

### 6. 完了報告

作ったファイル・変更したファイルの絶対パス、`built:` の件数、`check` の要約、自動再構築の有無を報告し、本体の run manifest に追記する。

## アンインストール

1. 登録した自動再構築のジョブを解除する
2. AI ガイドの `vault-search` 管理ブロックを取り除く
3. `VAULT_SEARCH_VAULT` などの環境変数を消す
4. `~/.local/share/vault-search/`（Windows は `%LOCALAPPDATA%\vault-search\`）を削除する

ノートには書き込んでいないので、Vault 側の後始末は要りません。
