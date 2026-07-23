# Claude Code × Obsidian セットアップ指示書

> **このファイルを受け取った方へ**: これは Claude Code に読ませる指示書です。ターミナルで Claude Code を起動して、
> 「**このファイル（パスを指定）を読んで、書いてある通りにセットアップを進めて**」
> と言うだけで、Obsidian のインストールから連携設定まで Claude が進めてくれます。
> 途中、アプリの画面操作（クリック）が必要な箇所だけ Claude が手順を案内するので、その通り操作してください。

---

**ここから下は Claude Code への指示です。**

あなた（Claude Code）はこの指示書に従い、ユーザーの環境（macOS または Windows。Linux は実験的対応。コマンド例は macOS/bash 表記なので、Windows では PowerShell に読み替える）に「Claude Code × Obsidian 連携」をセットアップする。ユーザーは Claude Code を使い始めたばかりで、Obsidian も初心者の可能性がある。専門用語には一言説明を添え、進捗を日本語でこまめに報告すること。

## 動作確認環境（2026-07 / v1.1.0 時点）

- Claude Code: 2.x 系（スキル・プラグイン対応版）
- Obsidian: インストーラ **1.12.7 以上**（Obsidian CLI に必要）
- 公式スキル: `kepano/obsidian-skills`（プラグイン形式。収録5スキル）
- OS: macOS / Windows（Linux は実験的）

> バージョンや収録スキル数は変わりうる。数字が合わなくなったらこのブロックと該当ステップだけ直せばよい。各ステップ本文は「最新を確認する」方針で書いてある。

## 進め方の原則

- 各ステップは **確認 → 実行 → 検証** の順。すでに完了しているステップは実行せずスキップし、「済んでいたので飛ばした」と報告する
- **既存ファイルを上書きしない**。同名ファイルがあれば中身を見せて、ユーザーに確認してから進める
- GUI 操作（Obsidian の画面でのクリック）はユーザーにやってもらう。手順を番号付きで示し、完了の返事を待ってから次へ進む
- コマンドが失敗したら、エラーを見て代替手段（このファイル内に記載）を試す。それでもダメなら状況を報告して指示を仰ぐ

## Step 0: ヒアリングと環境確認

まずユーザーに以下をまとめて聞く（質問攻めにせず、1回のやりとりで。答えにくそうなら例を出して助ける）:

1. **仕事の内容**（一言で）と、**いま動いている案件・繰り返しやる作業**を2〜3個 — これがそのまま Vault のフォルダ構成（Step 4 のルーティング表）になる
2. **Claude にどんな手伝いを期待するか** — 例: 文書のドラフト、調べもの、会議メモの整理、考えの壁打ち。→ Step 6 でグローバル設定に書き込む
3. **Vault（ノート置き場）をどこに作るか** — デフォルト提案: `~/Documents/Obsidian Vault`。既に Obsidian を使っていて Vault があるなら、そのパスを教えてもらう
4. **保存モード** — 成果をどう Vault に残すか3択で聞く。①自動保存 ②保存前に確認（おすすめ）③`/vault-save` を実行したときだけ。迷う人・機密案件や委託先の情報を扱う人は②が安全。→ Step 6 で反映する

フォルダが思いつかない場合は `inbox/`（分類前の一時置き場）と `メモ/` だけで始めてよい（あとから増やせる）。

並行して環境を確認する:

- OS の判定（macOS / Windows / Linux。以降のコマンドはこれに合わせる）
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

Obsidian CLI は、ターミナル（つまりあなた＝Claude）から Obsidian を操作できる公式ツール。検索・ノート作成・タグ一覧などができる。

1. ユーザーに GUI 操作を案内する:
   - Obsidian の **設定（Settings）→ 一般（General）**
   - 「**Command line interface**」をオンにする
   - 表示されるプロンプトに従って CLI を登録してもらう
2. 検証: `obsidian help` を実行して使い方が表示されること（**Obsidian アプリが起動中であることが前提**。以後もそう）
3. 失敗したら: インストーラが 1.12.7 未満の可能性が高い。Step 1 の注意に従い最新インストーラを入れ直してもらってから再試行

## Step 4: Vault 直下に CLAUDE.md（AI用の地図）を置く

`CLAUDE.md` は Claude Code がそのフォルダで作業するとき自動で読み込む指示書。Vault 直下に置くと、「このVaultの構成・保存規約」を毎回説明し直さなくてよくなる。

付録A のテンプレートを `<Vaultパス>/CLAUDE.md` に書き込む。その際:

- `〈あなたの名前〉` はユーザーの名前に置き換える（聞く）
- ルーティング表の行は Step 0 で聞いた案件・作業に合わせて書き換える（用途欄にはヒアリングで聞いた内容を一言で書く。AIが保存先を迷わないための地図なので、具体的なほどよい）
- 規約セクションはテンプレのまま使う

既存ファイルがある場合は、変更前に同じディレクトリへ `CLAUDE.md.backup-YYYYMMDD-HHMMSS` を作り、差分と統合案を見せて了承を得る。新規作成か更新かをセットアップ記録へ残す。

書き込んだら、ルーティング表・規約の意味を 3行程度でユーザーに説明する（詳しい「なぜ」は付録C を要約して伝える）。

### 任意: Codex 等からも同じガイドを読む

ユーザーが Codex など `AGENTS.md` を読むエージェントも使うなら、Vault直下に `AGENTS.md` を用意する:

- macOS / Linux: 既存 `AGENTS.md` が無ければ、Vault内で `ln -s CLAUDE.md AGENTS.md`
- Windows: シンボリックリンクを無理に作らず、`AGENTS.md` に「このフォルダの `CLAUDE.md` を読んで従う」と短く書く
- 既存 `AGENTS.md` がある場合は上書きせず、内容を確認して統合案を出す

## Step 5: /vault-save スキルを作る

Claude Code のスキルは、特定作業の手順を再利用可能にする仕組み。`~/.claude/skills/vault-save/SKILL.md` に置き、会話の成果を規約どおりに Vault へ保存する `/vault-save` を作る。

1. `~/.claude/skills/vault-save/` ディレクトリを作成（無ければ）
2. 付録B のテンプレートを `~/.claude/skills/vault-save/SKILL.md` に書き込む。`/path/to/YourVault/` は実際の Vault パスに置き換える（`~/Documents/Obsidian Vault/` のような `~` 表記でよい）
3. 既存の `~/.claude/commands/vault-save.md` がある場合は、内容を比較してSkill版へ移行する提案を出す。確認なしで削除しない
4. 検証: frontmatterに `name: vault-save` と `disable-model-invocation: true` があり、Vaultパスのプレースホルダーが残っていないこと
5. ユーザーに「次回の Claude Code 起動から `/vault-save` が使える」と伝える

## Step 6: グローバル CLAUDE.md に保存ルールを追記

ここが連携の肝。`~/.claude/CLAUDE.md`（全プロジェクト共通で毎回読まれる個人設定）に Vault の存在と保存モードを書く。これが無いと、Vault の外で作業したとき Claude は Vault の存在自体を知らない。

1. `~/.claude/CLAUDE.md` が既にあれば、変更前に `~/.claude/CLAUDE.md.backup-YYYYMMDD-HHMMSS` を作る。中身と差分を見せ、追記・更新の了承を取る。無ければ新規作成
2. 以下の**管理ブロック**を追記する。再実行時に同じ開始・終了コメントがあれば二重追記せず、そのブロックだけ更新する。`/path/to/YourVault/` は実際のパス、`〈…〉` はヒアリング結果、`〈保存モード文〉` はStep 0の選択で置き換える:

```markdown
<!-- claude-obsidian-setup:start -->
## ユーザープロフィール

- 仕事: 〈仕事の内容〉
- いま動いている案件: 〈案件・繰り返し作業〉
- Claude への期待: 〈どんな手伝いをしてほしいか〉

## Obsidian Vault への記録

- Vault: /path/to/YourVault/（フォルダ構成・規約は Vault 直下の CLAUDE.md を読む）
- 保存モード: 〈下記3モードのうち選んだ1行〉
- 保存の目安は「あとで読み返す価値があるか」。調べものの途中経過は保存せず、結論が出た時点で1枚にまとめる
- 保存規約（frontmatter description 1行・MOCと関連ノートへのリンク・未確認情報の［要確認］印）は Vault 直下 CLAUDE.md に従う
- コードそのもの・雑談は保存しない
- APIキー・パスワード・認証トークンは保存しない
- 他社・顧客の機密情報は自動保存しない。個人情報を含む場合は保存前に確認する
<!-- claude-obsidian-setup:end -->
```

`〈保存モード文〉` は次から1行を使う:

- 自動保存: `実質的な成果が出たら、指示を待たず Vault に保存し、保存後にパスを1行報告する`
- 保存前に確認: `実質的な成果が出たら保存先を提案し、ユーザーの確認後に Vault へ保存する`
- 明示実行のみ: `ユーザーが /vault-save または明示的な保存指示を出したときだけ Vault へ保存する`

3. ユーザーに選んだモードを説明する。止めたいときは管理ブロック（開始コメントから終了コメントまで）を削除すればよいと伝える

## Step 7: 公式 Obsidian スキルの導入

Obsidian の CEO（kepano）公開の Claude Code 用公式スキル集を入れる。スキル＝特定作業のやり方を Claude に教える説明書パックで、wikilink・callout・frontmatter などの Obsidian 記法を正しく扱えるようになる。

1. **導入前レビュー**: `https://github.com/kepano/obsidian-skills` のREADME・`.claude-plugin/plugin.json`・`.claude-plugin/marketplace.json` と各 `SKILL.md` を確認する。想定外のshell実行、過剰なツール権限、外部送信があれば止めてユーザーへ報告する。確認したcommit hashをセットアップ記録へ残す
2. Claude Code のプラグイン機能で導入する:

   ```bash
   claude plugin marketplace add kepano/obsidian-skills
   claude plugin install obsidian@obsidian-skills
   ```

   対話中のスラッシュコマンドを使う場合は、上記に相当する `/plugin marketplace add kepano/obsidian-skills` → `/plugin install obsidian@obsidian-skills` でもよい。
3. 検証: `claude plugin list` で `obsidian@obsidian-skills` がインストール済みであること。次回セッションから有効になる場合は再起動を案内する
4. プラグイン機能が使えない旧版では、最新版Claude Codeへの更新を案内する。更新できない場合だけ、上流READMEの手動導入手順に従う

Codexも使う場合は、同じ上流READMEのCodex手順（`skills/` を通常 `~/.codex/skills` へ配置）を案内する。Claude Code用プラグインと混同しない。

## Step 8: 動作確認とデモ

最後に一連の流れを実際に動かして見せる:

1. `obsidian vault` や `obsidian search query="test"` など CLI を1〜2個実行して疎通確認
2. デモとしてテストノートを1枚、規約どおりに作る:
   - `inbox/` に `セットアップ記録（YYYY-MM-DD）.md` のようなノートを作成
   - frontmatter に `description:` 1行を付ける
   - 本文にこの日セットアップした内容を箇条書きで記録
3. ユーザーに Obsidian の画面でそのノートが見えることを確認してもらう
4. 次の設定検査を行う:
   - `~/.claude/CLAUDE.md` の管理ブロックがちょうど1組
   - `~/.claude/skills/vault-save/SKILL.md` にプレースホルダーが残っていない
   - Vault直下 `CLAUDE.md` のルーティング表に実在フォルダが載っている
   - `claude plugin list` にObsidianスキルがある
5. `inbox/セットアップ記録（YYYY-MM-DD）.md` に、選択した保存モード、変更・作成ファイル、バックアップ、確認した外部スキルcommitを記録する

## 完了報告

すべて終わったら、以下をまとめて報告する:

- 何をどこにセットアップしたか（パス一覧）
- 変更前バックアップのパス
- 選択した保存モード
- スキップしたステップとその理由
- 明日からの使い方:
  1. **選択した保存モードで記録される** — 自動 / 保存前に確認 / 明示実行のみのどれを選んだかを再掲する
  2. 明示的に保存したいときは `/vault-save`（保存先の確認あり）
  3. Vault のフォルダで `claude` を起動すれば、Vault の構成を理解した状態で相談・整理ができる
  4. フォルダを増やしたら Vault 直下 `CLAUDE.md` のルーティング表も更新する（Claude に頼めばよい）
- 付録C（運用ルールの「なぜ」）の要約
- 下記「アンインストール」の手順

---

## 付録A: Vault 直下 CLAUDE.md テンプレート

```markdown
# Vault ガイド（AI用ルーティング）

この Vault は〈あなたの名前〉の知識ベース。このファイルは Claude 等の AI 用の地図。

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

> MOC = Map of Content。フォルダの入口になる目次ノートのこと。ノートが10枚を超えたフォルダから作れば十分（Claude に「このフォルダのMOCを作って」と頼めばよい）。

## 付録B: ~/.claude/skills/vault-save/SKILL.md テンプレート

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

## 付録C: 運用ルールの「なぜ」（セットアップ後にユーザーへ説明する）

**(1) description は AI の目次** — AIは毎回 Vault 全体を読み込めない（量的に無理）。各ノート先頭の `description:` 1行が AI にとっての「背表紙」になり、数百ノート規模になってもこの1行の集合が地図として機能する。書くのは AI 自身なので人間の手間はゼロ。

**(2) リンクのないノートは存在しないのと同じ** — AI に保存させると「保存して終わり」の孤児ノートが量産されがち。規約で「保存＝MOCに1行＋関連ノートへ wikilink」までをワンセットにする。`/vault-save` にはこの手順が組み込み済み。

**(3) ［要確認］印は未来の自分への保険** — AI は時々もっともらしい嘘を書く。怖いのは書いた瞬間ではなく、数週間後に別セッションの AI がそのノートを「確定した事実」として引用するとき。未確認の数字・固有名詞に印を付けるだけで事故率が大きく下がる。

**発展編（軌道に乗ってから、ユーザーが望んだら）** — 目安としてノートが100枚を超えた頃に一度提案するとよい: ①SQLite FTS5 による全文検索インデックス ②Vault の git 管理＋自動コミット（AI に大量編集させる前の復元点） ③孤児ノート・description 未記入の定期チェック。いずれも最初は不要。

---

## アンインストール

ユーザーが連携を止めたい場合は、変更一覧とバックアップを確認してから次を行う。既存ファイル全体を削除してはいけない。

1. `~/.claude/CLAUDE.md` から `<!-- claude-obsidian-setup:start -->` 〜 `<!-- claude-obsidian-setup:end -->` の管理ブロックだけを削除
2. `~/.claude/skills/vault-save/` を、このセットアップで新規作成した場合だけ削除。既存Skillを更新した場合はバックアップから戻す
3. `claude plugin uninstall obsidian@obsidian-skills` でプラグインを外す（他でも利用中なら残す）
4. 任意で追加した `AGENTS.md` を、このセットアップで新規作成した場合だけ削除
5. VaultのMarkdownノートはユーザーのデータなので削除しない。デモノートも削除前に確認する
6. 必要ならバックアップから `CLAUDE.md` を復元する

完了後、「削除したもの」「残したもの」「復元したもの」を報告する。
