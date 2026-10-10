# research-template

**1 リポジトリ = 1 研究プロジェクト**として、実験の試行錯誤からデータ解析・図表生成・原稿執筆までを 1 つのリポジトリで完結させるための、研究プロジェクト用テンプレートです。

- この **README.md は人間向けの入口ドキュメント(日本語)** です。
- コーディングエージェント(Claude Code / Codex CLI など)向けの指示は **`AGENTS.md`(英語)が正典**です。詳細は「[文書整備の方針](#文書整備の方針)」を参照してください。

## このテンプレートの目的と研究方針

新しい研究を、再現可能な形で素早く始めるための共通土台です。このテンプレートから作られたプロジェクトでは、次の方針を守ります。

1. **再現性第一** — すべての結果(図・表・数値)は、コードから再生成できる状態を保つ。
2. **`data/raw/` は不変(イミュータブル)** — 生データは手で編集しない。Git には構造のみ残し、大容量ファイルはコミットしない。
3. **派生データは再生成する** — `data/interim/`・`data/processed/` はスクリプトの出力。直接編集せず、必要ならコードを直して再生成する。
4. **再利用コードは `src/`、スクリプトは薄く** — 共有ロジックは `src/` に置き、`scripts/` は再利用関数を呼び出すだけのエントリポイントにする。
5. **実験は `exp/` に番号付きで蓄積** — 試行錯誤は `exp/NNN_<slug>/` の自己完結ディレクトリとして積み上げる。過去の実験は書き換えず、条件を変えるなら新しい番号で作る。
6. **`result/` は生成物** — 図表は手で編集せず、コードから再生成する。
7. **実行環境は Docker + uv に統一** — 依存環境はイメージ内の `/opt/venv` に置き、ホストに `.venv` を作らない。ホストの Python には依存しない。
8. **原稿のみホストの LuaLaTeX** — `draft/` 以下のコンパイルはコンテナではなくホストで行う。

## 新しいプロジェクトの始め方(初期設定)

### 1. リポジトリを作成する

GitHub の **「Use this template」** からの作成を推奨します。手動で行う場合:

```bash
git clone <このテンプレートの URL> my-research
cd my-research
rm -rf .git
git init
git remote add origin <新プロジェクトの URL>
```

### 2. プロジェクト名を変更する

| 対象 | 変更 | 理由 |
|---|---|---|
| `pyproject.toml` の `name`・`description` | **変更する** | uv プロジェクトの識別名 |
| `docker-compose.yml` の `container_name`・`image` | **変更する** | ホスト全体で一意である必要があり、共有すると他プロジェクトと衝突する |
| `docker-compose.yml` のサービスキー `research-template` | **変更しない** | サービス名は compose プロジェクト内スコープなので衝突しない。据え置けば README・`AGENTS.md` 内のすべてのコマンドがそのまま動く |
| `README.md` のタイトル・冒頭説明 | **変更する** | プロジェクトの内容に合わせて書き換える |

`pyproject.toml` の `name` を変えたら、最初のビルドの前に `uv.lock` も更新します。ビルドは `uv.lock` の固定版をそのまま入れるので、古いままだと `Missing workspace member` で止まります。ホストに Python 環境を作らないよう、uv だけのコンテナで実行します。

```bash
make lock
```

### 3. 環境変数を設定する

```bash
cp .env.example .env
id -u; id -g   # 出力に合わせて .env の UID / GID を設定
```

他のプロジェクトとポートが衝突する場合は、`.env` で `HOST_JUPYTER_PORT` を変更してください(既定 8889)。

### 4. イメージをビルドし、コンテナを起動する

```bash
docker compose build
docker compose up -d
```

依存パッケージは `uv.lock` から**イメージのビルド時に**イメージ内の `/opt/venv` へ入ります。`HOME` と uv のキャッシュは Docker の名前付きボリュームに置くので、マウントした作業ディレクトリ(ホスト側)に `.venv`、uv のキャッシュ、`__pycache__` は作られません。`pyproject.toml`・`uv.lock` を変えたら、`docker compose build` でイメージを作り直します。

### 5. 動作確認

```bash
docker compose exec research-template uv run pytest
```

全テスト(設定、実行環境、原稿の構造)が通れば環境構築は完了です。

### 6. 最初のコミット

リネームした一式と、`make lock` で更新した `uv.lock` をコミットします。

## ディレクトリ構成

```text
research-template/
├── src/                   # 再利用可能なソースコード
│   ├── utils/             # 汎用ユーティリティ(パス・数学・描画・検証・乱数・I/O)
│   ├── models/            # ドメインオブジェクト・データコンテナ・ローダ・パーサ
│   ├── methods/           # 解析手法・統計処理・アルゴリズム・モデリング
│   └── analysis/          # 上記を組み合わせた高次の解析ワークフロー
├── scripts/               # 実行用エントリポイント(ロジックは持たせない)
├── exp/                   # 番号付き実験ディレクトリ(自己完結・試行錯誤の蓄積)
│   └── _template/         # 新しい実験の雛形(cp -r で複製して使う)
├── tests/                 # pytest テストスイート
├── data/
│   ├── raw/               # 生データ(不変。Git には構造のみ)
│   ├── interim/           # 中間生成データ
│   └── processed/         # 解析可能な派生データ
├── result/
│   ├── figures/           # 生成された図
│   ├── tables/            # 生成された表
│   └── animations/        # 生成されたアニメーション・動画
├── draft/                 # 原稿(LuaLaTeX。compile.sh でビルド、luatexja で日本語執筆可)
├── docs/                  # 人間向けドキュメント(研究ログ・意思決定記録)
├── .claude/               # Claude Code のスキル
├── AGENTS.md              # エージェント向け指示の正典(英語)
├── CLAUDE.md              # AGENTS.md への参照のみ(内容を書かない)
├── LICENSE                # MIT License
├── config.py              # 共有パス・乱数シード(42)・図の設定(DPI 等)
├── .env.example           # .env の雛形(UID/GID, DATA_ROOT, HOST_JUPYTER_PORT)
├── Dockerfile
├── docker-compose.yml     # CPU のみのベース構成
├── docker-compose.gpu.yml # NVIDIA GPU 用オーバーライド
├── pyproject.toml
└── uv.lock                # コミット対象(uv add / remove 後に更新をコミット)
```

## 日常操作コマンド

### コンテナ操作

```bash
docker compose build                            # 初回と、pyproject.toml・uv.lock を変えた後
docker compose up -d                            # 初回起動・設定変更後の再作成
docker compose start                            # 停止中のコンテナを再開
docker compose stop                             # 停止
docker compose exec research-template bash      # コンテナに入る(必要な場合のみ)
```

### Python の実行とパッケージ管理

```bash
docker compose exec research-template uv run python scripts/<script>.py
docker compose exec research-template uv add <package>
```

`uv add` / `uv remove` の後は、`docker compose build` でイメージにも反映し、更新された `uv.lock` をコミットしてください。

### テスト

```bash
docker compose exec research-template uv run pytest
```

テストは、解析の正しさを担保するもの(既知の答えを持つ合成データでの推定、単位・分母・丸めの独立計算との照合、再現手順の誤入力停止など)と、システム上の制約を守るものに絞ります。初めから入っているのは次の3つです。

- `tests/test_config.py` — 共有パスと設定
- `tests/test_runtime_constraints.py` — Docker 内で動いていること、依存環境・キャッシュが作業ディレクトリの外にあること、生データが読み取り専用であること
- `tests/test_manuscript_structure.py` — 原稿の引用キー・参照ラベル・読み込むファイルと図が存在すること。章立て・語数・文言・主張は固定しません(文章は著者が確かめます)

### Jupyter(任意)

Jupyter は依存に含まれていません。使う場合は追加してから起動します。

```bash
docker compose exec research-template uv add jupyterlab
docker compose exec research-template uv run jupyter lab --ip 0.0.0.0 --port 8888 --no-browser
```

ホスト側からは `http://localhost:8889`(`.env` の `HOST_JUPYTER_PORT` で変更可)でアクセスします。

### 原稿(LuaLaTeX、ホストで実行)

```bash
bash draft/compile.sh            # draft/main.pdf と draft/supplementary.pdf(make tex でも可)
bash draft/compile.sh --review   # 行番号とダブルスペース入りの draft/main_review.pdf(make tex-review)
```

`compile.sh` は `lualatex` → `bibtex`(参考文献を宣言し、引用がある文書だけ) → `lualatex` → `lualatex` を `main.tex` と `supplementary.tex` に対して実行し、中間ファイルはすべて Git 管理外の `draft/build/` に書いて、PDF だけを `draft/` に残します。`draft/` の中で `lualatex` を手で実行しないでください。そこに残った古い `.aux`・`.bbl` が次のビルドで黙って読まれ、参考文献や参照が欠けた PDF ができます。

査読用の版(`--review`)は本文が同じで、`main.tex` の `\ifdefined\reviewformat` が書式だけを切り替えます。投稿時に行番号を求める誌が多いため用意しています。

原稿の数値と表は手で書かず、`result/tables/` の CSV からコードで LaTeX のマクロや表のファイルを書き出して `\input` します(CSV の検査が通っても、手で書き写した数値は古いまま残るため)。

`draft/main.tex`・`draft/supplementary.tex` は見出しのみの雛形です。luatexja + 原ノ味フォントを読み込んでおり、日本語でも執筆できます。

### GPU(任意)

ベース構成は CPU のみです。NVIDIA GPU を使うマシンでは:

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
```

## 実験の回し方

試行錯誤の実験は `exp/` 以下に番号付きディレクトリとして蓄積します。詳細な規約は [`exp/README.md`](exp/README.md) を参照してください。

1. **雛形をコピーする**(番号は既存の最大値 + 1):

   ```bash
   cp -r exp/_template exp/001_<slug>
   ```

2. **`params.py` を編集**してパラメータ(シード等)を決める。
3. **`run.py` を実装**する。ロジックは `src/` の再利用コードを呼び出す形にし、冒頭の sys.path ブートストラップは残す。
4. **実行する**:

   ```bash
   docker compose exec research-template uv run python exp/001_<slug>/run.py
   ```

   出力(図・ログ・中間データ)はすべて `exp/001_<slug>/out/` に保存されます(Git 管理外)。

5. **結果と考察を `exp/001_<slug>/README.md` に記録**する。
6. **採用が決まった図は `result/figures/` へ昇格**する。手コピーではなく、`run.py` の最終処理または `scripts/` のスクリプトでコードとしてコピー・再出力する。

## データの扱い

- **コンテナ内**では、`docker-compose.yml` が `./data/raw` を `/data` に**読み取り専用**でマウントし、常に `DATA_ROOT=/data` を設定します。同じデータは作業ディレクトリ経由(`/workspace/data/raw`)でも見えるため、そこにも読み取り専用で重ね、どちらの経路からも書き換えられないようにしています。
- **ホスト側**で `config.py` を使う場合は、`.env` の `DATA_ROOT`、未設定なら `./data/raw` にフォールバックします。
- 入力データは `data/raw/` に置きます。大容量ファイル(`.nc`, `.h5`, `.parquet` など)は `.gitignore` 済みで、Git には入りません。

## 文献

- 書誌の正は `draft/reference.bib` だけです。文献管理ソフトとは同期しません。
- エージェントは Zotero などの文献管理ソフトに接続しません。自分のライブラリの書誌が要るときは、BibTeX などで書き出してエージェントに渡します。
- 書誌を足すときは、エージェントが見つけたものも渡されたものも、DOI から原典(出版社のページ、PMC、Crossref、保存版)と照合してから入れます。引用する数値も原文で確かめます。

## Git 運用

- **`main` は保護ブランチ**です(GitHub ruleset により PR 必須・承認 1 人・force push 禁止・ブランチ削除禁止)。
- 作業はフィーチャーブランチで行い、PR で `main` にマージします。PR の承認・マージ判断はオーナーが管理します。
- オーナー(リポジトリ admin)には **PR 経由に限定した bypass** があり、自分の PR は承認なしでマージできます(GitHub では自分の PR を自分で承認できないため)。直接 push はオーナーを含む全員がブロックされます。
- このテンプレートから作った新リポジトリでも、最初の push 後に同じ保護を設定します:

  ```bash
  gh api repos/<owner>/<repo>/rulesets -X POST --input - <<'JSON'
  {
    "name": "protect-main",
    "target": "branch",
    "enforcement": "active",
    "bypass_actors": [
      { "actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "pull_request" }
    ],
    "conditions": { "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] } },
    "rules": [
      { "type": "deletion" },
      { "type": "non_fast_forward" },
      { "type": "pull_request",
        "parameters": {
          "required_approving_review_count": 1,
          "dismiss_stale_reviews_on_push": false,
          "require_code_owner_review": false,
          "require_last_push_approval": false,
          "required_review_thread_resolution": false } }
    ]
  }
  JSON
  ```

## 文書整備の方針

このテンプレートでは、文書の役割を次のとおり分離します。

| ファイル | 言語 | 役割 | 更新ルール |
|---|---|---|---|
| `README.md` | 日本語 | 人間向けの入口(方針・手順・コマンド) | 構成やワークフローの変更時に `AGENTS.md` と**同時に**更新する |
| `AGENTS.md` | 英語 | エージェント向け指示の**正典** | 運用ルールの変更は必ずここに書く |
| `CLAUDE.md` | — | `See @AGENTS.md` の**ポインタのみ** | **内容を追加しない**。編集は常に `AGENTS.md` へ |
| `docs/` | 日本語 | 研究ログ・意思決定記録など人間向け文書の蓄積場所 | 随時追記。使い方は [`docs/README.md`](docs/README.md) |
| `exp/*/README.md` | 日本語 | 各実験の目的・方法・結果・考察 | 実験の作成時と、意味のある実行のたびに追記 |

**更新のトリガー:**

- ディレクトリ構成・実行環境・ワークフロールールを変えたら、`README.md` と `AGENTS.md` をセットで更新する(片方だけ直して不整合を残さない)。
- 「なぜそうしたか」という判断や経緯は `docs/` に記録する。雛形は [`docs/templates/`](docs/templates/) にあります。

## ライセンス

このリポジトリに含まれるコード、設定ファイル、文書・原稿の雛形は [MIT License](LICENSE) で公開しています。

このテンプレートから作成した研究リポジトリに後から追加される研究データ、個別の論文原稿、図表、第三者由来の素材へ MIT License が自動的に適用されるわけではありません。それぞれの権利者、データ提供元、共同研究契約、倫理審査、投稿規程に従って、公開範囲とライセンスを個別に定めてください。

## Claude Code スキル

- **`/session-save`** — セッションでの作業内容をメモリと `.claude/sessions/` 以下の Markdown ログに保存します。
