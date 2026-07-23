# Claude Code / Codex × Obsidian セットアップ指示書

> **このファイルを受け取った方へ**: これは Claude Code または Codex に読ませる指示書です。ターミナルで使いたいエージェントを起動して、
> 「**このファイル（パスを指定）を読んで、書いてある通りにセットアップを進めて**」
> と言うだけで、Obsidian のインストールから連携設定までエージェントが進めてくれます。
> 途中、アプリの画面操作（クリック）が必要な箇所だけ手順を案内するので、その通り操作してください。

---

**ここから下は Claude Code / Codex への指示です。**

あなた（Claude Code または Codex）はこの指示書に従い、ユーザーの環境（macOS または Windows。Linux は実験的対応。コマンド例は macOS/bash 表記なので、Windows では PowerShell に読み替える）に「AIエージェント × Obsidian 連携」をセットアップする。ユーザーはAIエージェントを使い始めたばかりで、Obsidian も初心者の可能性がある。専門用語には一言説明を添え、進捗を日本語でこまめに報告すること。

最初に、自分が Claude Code と Codex のどちらで実行されているかを判定する。以降は次の呼称を使う:

- **実行エージェント**: 現在この指示書を読んでいる Claude Code または Codex
- **セットアップ対象**: Step 0 で選ぶ「Claude Codeのみ」「Codexのみ」「両方」のいずれか
- **明示呼び出し**: Claude Code は `/vault-save`、Codex は `$vault-save`

## 動作確認環境（2026-07 / v1.2.0 時点）

- Claude Code: 2.x 系（スキル・プラグイン対応版）
- Codex CLI: 0.144.6（`AGENTS.md`・Agent Skills対応版）
- Obsidian: インストーラ **1.12.7 以上**（Obsidian CLI に必要）
- 公式スキル: `kepano/obsidian-skills`（プラグイン形式。収録5スキル）
- OS: macOS / Windows（Linux は実験的）

> バージョンや収録スキル数は変わりうる。数字が合わなくなったらこのブロックと該当ステップだけ直せばよい。各ステップ本文は「最新を確認する」方針で書いてある。

## 進め方の原則

- 各ステップは **確認 → 実行 → 検証** の順。すでに完了しているステップは実行せずスキップし、「済んでいたので飛ばした」と報告する
- **既存ファイルを上書きしない**。同名ファイルがあれば中身を見せて、ユーザーに確認してから進める
- Claude Code用とCodex用の設定先を混同しない。対象外のエージェントの設定は変更しない
- GUI 操作（Obsidian の画面でのクリック）はユーザーにやってもらう。手順を番号付きで示し、完了の返事を待ってから次へ進む
- コマンドが失敗したら、エラーを見て代替手段（このファイル内に記載）を試す。それでもダメなら状況を報告して指示を仰ぐ

## Step 0: ヒアリングと環境確認

まずユーザーに以下をまとめて聞く（質問攻めにせず、1回のやりとりで。答えにくそうなら例を出して助ける）:

1. **仕事の内容**（一言で）と、**いま動いている案件・繰り返しやる作業**を2〜3個 — これがそのまま Vault のフォルダ構成（Step 4 のルーティング表）になる
2. **AIエージェントにどんな手伝いを期待するか** — 例: 文書のドラフト、調べもの、会議メモの整理、考えの壁打ち。→ Step 6 でグローバル設定に書き込む
3. **Vault（ノート置き場）をどこに作るか** — デフォルト提案: `~/Documents/Obsidian Vault`。既に Obsidian を使っていて Vault があるなら、そのパスを教えてもらう
4. **保存モード** — 成果をどう Vault に残すか3択で聞く。①自動保存 ②保存前に確認（おすすめ）③明示呼び出し（Claude Codeは `/vault-save`、Codexは `$vault-save`）のときだけ。迷う人・機密案件や委託先の情報を扱う人は②が安全。→ Step 6 で反映する
5. **セットアップ対象** — ①現在の実行エージェントのみ（おすすめ）②Claude CodeとCodexの両方。現在使っていない側まで勝手に設定しない

フォルダが思いつかない場合は `inbox/`（分類前の一時置き場）と `メモ/` だけで始めてよい（あとから増やせる）。

並行して環境を確認する:

- OS の判定（macOS / Windows / Linux。以降のコマンドはこれに合わせる）
- 実行エージェントとバージョン（Claude Code: `claude --version`、Codex: `codex --version`）
- Obsidian インストール済みか（macOS: `/Applications/Obsidian.app`、Windows: `winget list Obsidian.Obsidian` またはスタートメニュー、Linux: `command -v obsidian` と導入方式を確認）
- `git` の有無（Step 7 の導入前レビューで使う。無ければGitHub上のファイルを個別確認）
- パッケージマネージャの有無（macOS: `which brew`、Windows: `winget` は標準搭載、Linux: ディストリビューションと導入済み方式を確認）

## Step 1: Obsidian のインストール（未導入の場合のみ）

- **macOS**: `brew install --cask obsidian`。Homebrew が無ければ https://obsidian.md/download から dmg を手動ダウンロードしてもらう（URL を提示して案内）
- **Windows**: `winget install Obsidian.Obsidian`。失敗したら同じく公式ページから手動ダウンロード
- **Linux（実験的）**: ディストリビューションと既存の導入方式を確認し、公式ダウンロードページのAppImage / deb等を案内する。勝手に方式を変更しない
- 検証: アプリ本体が存在し、起動できること

**既に Obsidian が入っている場合の注意**: Step 3 の CLI には **インストーラのバージョン 1.12.7 以上**が必要。バージョンは Obsidian の **設定 → 一般** に表示される「Installer version」をユーザーに読み上げてもらって確認する。古い場合はアプリ内の更新では不十分なことがあるので、https://obsidian.md/download から最新インストーラを入れ直してもらう（設定やノートは消えない）。

## Step 2: Vault の作成と初回起動

1. Step 0 で決めたパスに Vault フォルダを作り、その中に **ヒアリングで決めた案件フォルダ全部＋ `inbox/`** をこの時点で `mkdir -p` で作る（Step 4 のルーティング表はこのフォルダ構成をそのまま表にする）
2. ユーザーに GUI 操作を案内する:
   - Obsidian を起動
   - 「**Open folder as vault**（フォルダをVaultとして開く）」を選び、作ったフォルダを指定
   - 起動したら教えてもらう。**以降のステップが終わるまで Obsidian は起動したままにしてもらう**（Step 3 と Step 8 の CLI はアプリ起動中でないと動かない）

## Step 3: Obsidian CLI の有効化

Obsidian CLI は、ターミナル（つまり実行エージェント）から Obsidian を操作できる公式ツール。検索・ノート作成・タグ一覧などができる。

1. ユーザーに GUI 操作を案内する:
   - Obsidian の **設定（Settings）→ 一般（General）**
   - 「**Command line interface**」をオンにする
   - 表示されるプロンプトに従って CLI を登録してもらう
2. 検証: `obsidian help` を実行して使い方が表示されること（**Obsidian アプリが起動中であることが前提**。以後もそう）
3. 失敗したら: インストーラが 1.12.7 未満の可能性が高い。Step 1 の注意に従い最新インストーラを入れ直してもらってから再試行

## Step 4: Vault 直下にAI用の地図を置く

Claude Code は `CLAUDE.md`、Codex は `AGENTS.md` をそのフォルダで作業するとき自動で読み込む。Vault 直下に置くと、「このVaultの構成・保存規約」を毎回説明し直さなくてよくなる。

セットアップ対象に応じて付録Aのテンプレートを書き込む:

- Claude Code: `<Vaultパス>/CLAUDE.md`
- Codex: `<Vaultパス>/AGENTS.md`
- 両方: 実行エージェント側のファイルを本体として作り、もう一方から同じ内容を読めるようにする

テンプレートを適用する際:

- `〈あなたの名前〉` はユーザーの名前に置き換える（聞く）
- ルーティング表の行は Step 0 で聞いた案件・作業に合わせて書き換える（用途欄にはヒアリングで聞いた内容を一言で書く。AIが保存先を迷わないための地図なので、具体的なほどよい）
- 規約セクションはテンプレのまま使う

既存ファイルがある場合は、変更前に同じディレクトリへ `<元ファイル名>.backup-YYYYMMDD-HHMMSS` を作り、差分と統合案を見せて了承を得る。新規作成か更新かをセットアップ記録へ残す。

書き込んだら、ルーティング表・規約の意味を 3行程度でユーザーに説明する（詳しい「なぜ」は付録C を要約して伝える）。

### 両方を使う場合

同じ規約の二重管理を避ける:

- macOS / Linux: もう一方のファイルが無ければ、本体への相対シンボリックリンクを作る（例: `ln -s CLAUDE.md AGENTS.md`）
- Windows: シンボリックリンクを無理に作らず、もう一方のファイルに「同じフォルダの `CLAUDE.md`（または `AGENTS.md`）を読んで従う」と短く書く
- 両方とも既存なら上書きやリンク化をせず、内容を確認して統合案を出す

## Step 5: vault-save スキルを作る

スキルは、特定作業の手順を再利用可能にする仕組み。セットアップ対象に応じて別々の場所へ作る。Claude Code版とCodex版は明示呼び出しの仕様が異なるため、シンボリックリンクで共有しない。

### Claude Codeが対象の場合

1. `~/.claude/skills/vault-save/` を作成し、付録B-1を `SKILL.md` に書き込む
2. 既存の `~/.claude/commands/vault-save.md` があれば、Skill版への移行を提案する。確認なしで削除しない
3. `name: vault-save`、`disable-model-invocation: true`、実際のVaultパスを検証する
4. 次回起動から `/vault-save` で使えると伝える

### Codexが対象の場合

1. `~/.agents/skills/vault-save/agents/` を作成し、付録B-2の `SKILL.md` と `agents/openai.yaml` を書き込む
2. 手作りする個人スキルは現行公式ドキュメントの `~/.agents/skills` に置く。`$CODEX_HOME/skills`（通常 `~/.codex/skills`）に同名スキルがあれば、内容を比較して重複を報告する
3. `name: vault-save`、`allow_implicit_invocation: false`、実際のVaultパスを検証する
4. Codexはスキル変更を通常自動検出する。見つからない場合は再起動し、`$vault-save` で使えると伝える

どちらのテンプレートでも `/path/to/YourVault/` は実際のVaultパスに置き換える（`~/Documents/Obsidian Vault/` のような `~` 表記でよい）。

## Step 6: グローバル指示に保存ルールを追記

ここが連携の肝。Vaultの外で作業していてもVaultの存在を認識できるように、セットアップ対象のグローバル指示へ保存モードを書く。

| 対象 | グローバル指示 | 管理ブロック |
|---|---|---|
| Claude Code | `~/.claude/CLAUDE.md` | `claude-obsidian-setup` |
| Codex | `$CODEX_HOME/AGENTS.md`（既定は `~/.codex/AGENTS.md`） | `codex-obsidian-setup` |

1. 対象ファイルが既にあれば、変更前に `<元ファイル名>.backup-YYYYMMDD-HHMMSS` を作る。中身と差分を見せ、追記・更新の了承を取る。無ければ新規作成
2. 以下の**管理ブロック**を対象ごとに追記する。再実行時に同じ開始・終了コメントがあれば二重追記せず、そのブロックだけ更新する
3. `〈管理名〉` は `claude-obsidian-setup` または `codex-obsidian-setup`、`〈AI名〉` は `Claude` または `Codex`、`〈ガイド名〉` は `CLAUDE.md` または `AGENTS.md`、`〈明示呼び出し〉` は `/vault-save` または `$vault-save` に置き換える:

```markdown
<!-- 〈管理名〉:start -->
## ユーザープロフィール

- 仕事: 〈仕事の内容〉
- いま動いている案件: 〈案件・繰り返し作業〉
- 〈AI名〉への期待: 〈どんな手伝いをしてほしいか〉

## Obsidian Vault への記録

- Vault: /path/to/YourVault/（フォルダ構成・規約は Vault 直下の 〈ガイド名〉 を読む）
- 保存モード: 〈下記3モードのうち選んだ1行〉
- 保存の目安は「あとで読み返す価値があるか」。調べものの途中経過は保存せず、結論が出た時点で1枚にまとめる
- 保存規約（frontmatter description 1行・MOCと関連ノートへのリンク・未確認情報の［要確認］印）は Vault 直下の 〈ガイド名〉 に従う
- コードそのもの・雑談は保存しない
- APIキー・パスワード・認証トークンは保存しない
- 他社・顧客の機密情報は自動保存しない。個人情報を含む場合は保存前に確認する
<!-- 〈管理名〉:end -->
```

`〈保存モード文〉` は次から1行を使う:

- 自動保存: `実質的な成果が出たら、指示を待たず Vault に保存し、保存後にパスを1行報告する`
- 保存前に確認: `実質的な成果が出たら保存先を提案し、ユーザーの確認後に Vault へ保存する`
- 明示実行のみ: `ユーザーが 〈明示呼び出し〉 または明示的な保存指示を出したときだけ Vault へ保存する`

4. ユーザーに選んだモードを説明する。止めたいときは対象の管理ブロックだけを削除すればよいと伝える
5. グローバル指示は新しいセッションで確実に読み込まれる。セットアップ完了後に対象エージェントを再起動するよう案内する

## Step 7: 公式 Obsidian スキルの導入

Obsidian の CEO（kepano）が公開するAgent Skillsを入れる。wikilink・callout・frontmatter などのObsidian記法を正しく扱えるようになる。

1. **導入前レビュー**: `https://github.com/kepano/obsidian-skills` のREADME・`.claude-plugin/plugin.json`・`.claude-plugin/marketplace.json` と各 `SKILL.md` を確認する。想定外のshell実行、過剰なツール権限、外部送信があれば止めてユーザーへ報告する。確認したcommit hashをセットアップ記録へ残す
2. セットアップ対象に応じて導入する

### Claude Code

```bash
claude plugin marketplace add kepano/obsidian-skills
claude plugin install obsidian@obsidian-skills
```

対話中なら `/plugin marketplace add kepano/obsidian-skills` → `/plugin install obsidian@obsidian-skills` でもよい。`claude plugin list` で検証する。プラグイン機能が使えない旧版では更新を案内し、更新できない場合だけ上流READMEの手動導入へ進む。

### Codex

Codex組み込みの `$skill-installer` を明示的に使い、`https://github.com/kepano/obsidian-skills` の `skills/<skill-name>` をすべてインストールする。組み込みインストーラは `$CODEX_HOME/skills`（通常 `~/.codex/skills`）へ配置する。利用できない場合だけ、上流リポジトリの `skills/` 直下にある各スキルディレクトリを `~/.agents/skills/` へコピーする。どちらの場合も `<インストール先>/<skill-name>/SKILL.md` という構造になっていることを検証する。

> Codexでは、組み込みインストーラの配置先 `$CODEX_HOME/skills` と、手作りスキル向けの `~/.agents/skills` の両方が使われる。Claude Code用のプラグインコマンドはCodexへ流用しない。

## Step 8: 動作確認とデモ

最後に一連の流れを実際に動かして見せる:

1. `obsidian vault` や `obsidian search query="test"` など CLI を1〜2個実行して疎通確認
2. デモとしてテストノートを1枚、規約どおりに作る:
   - `inbox/` に `セットアップ記録（YYYY-MM-DD）.md` のようなノートを作成
   - frontmatter に `description:` 1行を付ける
   - 本文にこの日セットアップした内容を箇条書きで記録
3. ユーザーに Obsidian の画面でそのノートが見えることを確認してもらう
4. セットアップ対象に応じて設定検査を行う:
   - Claude Code: `~/.claude/CLAUDE.md` の管理ブロックが1組、`~/.claude/skills/vault-save/SKILL.md` にプレースホルダーがない、`claude plugin list` にObsidianスキルがある
   - Codex: `$CODEX_HOME/AGENTS.md`（既定は `~/.codex/AGENTS.md`）の管理ブロックが1組、`~/.agents/skills/vault-save/SKILL.md` にプレースホルダーがない、`agents/openai.yaml` で暗黙呼び出しが無効、Obsidianスキルが `$CODEX_HOME/skills` または `~/.agents/skills/` にある
   - Vault直下の対象ガイドにあるルーティング表と実在フォルダが一致する
5. `inbox/セットアップ記録（YYYY-MM-DD）.md` に、選択した保存モード、変更・作成ファイル、バックアップ、確認した外部スキルcommitを記録する

## 完了報告

すべて終わったら、以下をまとめて報告する:

- 何をどこにセットアップしたか（パス一覧）
- 変更前バックアップのパス
- セットアップ対象（Claude Code / Codex / 両方）
- 選択した保存モード
- スキップしたステップとその理由
- 明日からの使い方:
  1. **選択した保存モードで記録される** — 自動 / 保存前に確認 / 明示実行のみのどれを選んだかを再掲する
  2. 明示的に保存したいときは、Claude Codeでは `/vault-save`、Codexでは `$vault-save`（保存先の確認あり）
  3. Vault のフォルダで `claude` または `codex` を起動すれば、Vault の構成を理解した状態で相談・整理ができる
  4. フォルダを増やしたら Vault 直下の `CLAUDE.md` / `AGENTS.md` のルーティング表も更新する（エージェントに頼めばよい）
- 付録C（運用ルールの「なぜ」）の要約
- 下記「アンインストール」の手順

---

## 付録A: Vault直下のAIガイドテンプレート

```markdown
# Vault ガイド（AI用ルーティング）

この Vault は〈あなたの名前〉の知識ベース。このファイルはAIエージェント用の地図。

## ルーティング表

| フォルダ | 用途 | 入口（MOC） | 備考 |
|---|---|---|---|
| メモ/ | 日々のメモ・成果物 | なし | |
| inbox/ | 分類前の一時置き場 | なし | あとで各フォルダへ移す |

## 規約

- **命名**: 日付は `YYYY-MM-DD` 形式。工程が続くものは `01_` などの番号prefix
- **frontmatter**: 全ノートの先頭に `description:` を1行付ける（ノートの中身が一言でわかる要約。AIが書く）
- **リンク**: 保存＝リンクまでワンセット。新しいノートは (1) 該当MOC（あれば）に1行追加 (2) 本文から関連ノート1〜3本へ [[wikilink]]
- **検証状態の明示**: AIが未確認の数字・固有名詞・伝聞・仮説を書くときは、本文に ［要確認］ / 仮説 と必ず印を付ける。確認済みなら出典と日付を短く添える
- **保存してよい**: 分析・調査結果・設計判断と理由・下書き・学び。保存しない: コードそのもの（gitにある）・雑談

## 更新義務

フォルダを新設・大きく再編したら、このルーティング表を必ず更新する。
```

> MOC = Map of Content。フォルダの入口になる目次ノートのこと。ノートが10枚を超えたフォルダから作れば十分（エージェントに「このフォルダのMOCを作って」と頼めばよい）。

## 付録B-1: Claude Code用 vault-save テンプレート

```markdown
---
name: vault-save
description: Save the current conversation outcome to the user's Obsidian Vault
disable-model-invocation: true
argument-hint: "[file name or topic]"
---

# /vault-save — Obsidian Vault に保存

会話の成果物や調査結果を Obsidian Vault に保存する。

## 引数

$ARGUMENTS にファイル名やトピックを指定（例: /vault-save プロジェクトA打合せメモ）。
引数がなければ、直近の会話内容から適切なファイル名を提案する。

## Vault情報

- パス: /path/to/YourVault/
- フォルダ構成は Vault 直下の CLAUDE.md（ルーティング表）を必ず読んで最新を確認する。ここにハードコードしない

## 手順

1. **保存内容の特定**: 直近の会話から保存すべき成果物を特定。指定がなければ「何を保存しますか？」と聞く
2. **保存先の決定**: Vault 直下 CLAUDE.md のルーティング表に従いフォルダを選ぶ。迷ったら inbox/ に入れる。保存前に「〈フォルダ〉/〈ファイル名〉.md に保存します。よいですか？」と確認
3. **ファイル作成**:
   - frontmatter に description: を1行必ず書く
   - 冒頭に実行日の `YYYY-MM-DD` を書く
   - 会話のコンテキストがなくても後から読んでわかるように書く
   - 未確認の数字・固有名詞・伝聞には ［要確認］ / 仮説 の印を付ける
   - 既存ファイルがあれば追記か新規作成かを確認
4. **リンク**: 該当MOC（あれば）に1行追加し、本文から関連ノート1〜3本へ [[wikilink]] を張る
5. **完了報告**: 保存先パスと内容の1行要約を伝える

## ルール

- 重要だと思ったものはどんどん保存してよい
- コードそのものは保存しない（gitにある）。設計判断・背景・学び・記録を保存する
- 既存の Vault ファイルと重複しないよう注意
- APIキー・パスワード・認証トークンは保存しない
- 他社・顧客の機密情報や個人情報は、保存前にユーザーへ確認する
```

## 付録B-2: Codex用 vault-save テンプレート

`~/.agents/skills/vault-save/SKILL.md`:

```markdown
---
name: vault-save
description: Save the current conversation outcome to the user's Obsidian Vault. Use only when the user explicitly invokes $vault-save.
---

# $vault-save — Obsidian Vault に保存

会話の成果物や調査結果を Obsidian Vault に保存する。

## 入力

ユーザーが `$vault-save` の後ろに書いたテキストを、ファイル名またはトピックの希望として扱う。
指定がなければ、直近の会話内容から適切なファイル名を提案する。

## Vault情報

- パス: /path/to/YourVault/
- フォルダ構成は Vault 直下の AGENTS.md（ルーティング表）を必ず読んで最新を確認する。ここにハードコードしない

## 手順

1. **保存内容の特定**: 直近の会話から保存すべき成果物を特定。指定がなければ「何を保存しますか？」と聞く
2. **保存先の決定**: Vault 直下 AGENTS.md のルーティング表に従いフォルダを選ぶ。迷ったら inbox/ に入れる。保存前に「〈フォルダ〉/〈ファイル名〉.md に保存します。よいですか？」と確認
3. **ファイル作成**:
   - frontmatter に description: を1行必ず書く
   - 冒頭に実行日の `YYYY-MM-DD` を書く
   - 会話のコンテキストがなくても後から読んでわかるように書く
   - 未確認の数字・固有名詞・伝聞には ［要確認］ / 仮説 の印を付ける
   - 既存ファイルがあれば追記か新規作成かを確認
4. **リンク**: 該当MOC（あれば）に1行追加し、本文から関連ノート1〜3本へ [[wikilink]] を張る
5. **完了報告**: 保存先パスと内容の1行要約を伝える

## ルール

- コードそのものは保存しない（gitにある）。設計判断・背景・学び・記録を保存する
- 既存の Vault ファイルと重複しないよう注意
- APIキー・パスワード・認証トークンは保存しない
- 他社・顧客の機密情報や個人情報は、保存前にユーザーへ確認する
```

`~/.agents/skills/vault-save/agents/openai.yaml`:

```yaml
policy:
  allow_implicit_invocation: false
```

## 付録C: 運用ルールの「なぜ」（セットアップ後にユーザーへ説明する）

**(1) description は AI の目次** — AIは毎回 Vault 全体を読み込めない（量的に無理）。各ノート先頭の `description:` 1行が AI にとっての「背表紙」になり、数百ノート規模になってもこの1行の集合が地図として機能する。書くのは AI 自身なので人間の手間はゼロ。

**(2) リンクのないノートは存在しないのと同じ** — AI に保存させると「保存して終わり」の孤児ノートが量産されがち。規約で「保存＝MOCに1行＋関連ノートへ wikilink」までをワンセットにする。`/vault-save` / `$vault-save` にはこの手順が組み込み済み。

**(3) ［要確認］印は未来の自分への保険** — AI は時々もっともらしい嘘を書く。怖いのは書いた瞬間ではなく、数週間後に別セッションの AI がそのノートを「確定した事実」として引用するとき。未確認の数字・固有名詞に印を付けるだけで事故率が大きく下がる。

**発展編（軌道に乗ってから、ユーザーが望んだら）** — 目安としてノートが100枚を超えた頃に一度提案するとよい: ①SQLite FTS5 による全文検索インデックス ②Vault の git 管理＋自動コミット（AI に大量編集させる前の復元点） ③孤児ノート・description 未記入の定期チェック。いずれも最初は不要。

---

## アンインストール

ユーザーが連携を止めたい場合は、変更一覧とバックアップを確認してから次を行う。既存ファイル全体を削除してはいけない。

1. Claude Code: `~/.claude/CLAUDE.md` から `<!-- claude-obsidian-setup:start -->` 〜 `<!-- claude-obsidian-setup:end -->` の管理ブロックだけを削除
2. Codex: `$CODEX_HOME/AGENTS.md`（既定は `~/.codex/AGENTS.md`）から `<!-- codex-obsidian-setup:start -->` 〜 `<!-- codex-obsidian-setup:end -->` の管理ブロックだけを削除
3. `~/.claude/skills/vault-save/` / `~/.agents/skills/vault-save/` は、このセットアップで新規作成した対象だけを削除。既存Skillを更新した場合はバックアップから戻す
4. Claude Codeでは `claude plugin uninstall obsidian@obsidian-skills` でプラグインを外す。CodexのObsidianスキルも他で利用していない場合だけ、セットアップ記録を基に今回追加したディレクトリを削除する
5. Vault直下の `CLAUDE.md` / `AGENTS.md` / シンボリックリンクは、このセットアップで新規作成したものだけを削除する。既存ファイルを統合した場合はバックアップから戻す
6. VaultのMarkdownノートはユーザーのデータなので削除しない。デモノートも削除前に確認する

完了後、「削除したもの」「残したもの」「復元したもの」を報告する。
