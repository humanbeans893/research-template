# research-template

**1 リポジトリ = 1 研究プロジェクト**として、実験の試行錯誤からデータ解析・図表生成・原稿執筆までを 1 つのリポジトリで完結させるための、研究プロジェクト用テンプレートです。

- この **README.md は人間向けの入口ドキュメント(日本語)** です。
- コーディングエージェント(Claude Code / Codex CLI など)向けの指示は **`AGENTS.md`(英語)が正典**です。詳細は「[文書整備の方針](#文書整備の方針)」を参照してください。

## このテンプレートの目的と研究方針

新しい研究を、再現可能な形で素早く始めるための共通土台です。このテンプレートから作られたプロジェクトでは、次の方針を守ります。

1. **再現性第一** — すべての結果(図・表・数値)は、コードから再生成できる状態を保つ。
2. **入力データは不変(イミュータブル)** — `data/raw/`(自分たちで取得した生データ)と `data/external/`(外部から入手したデータ)は手で編集しない。Git には構造のみ残し、大容量ファイルはコミットしない。
3. **派生データは再生成する** — `data/interim/`・`data/processed/` はスクリプトの出力。直接編集せず、必要ならコードを直して再生成する。
4. **再利用コードは `src/`、スクリプトは薄く** — 共有ロジックは `src/` に置き、`scripts/` は再利用関数を呼び出すだけのエントリポイントにする。
5. **実験は `experiments/` に番号付きで蓄積** — 試行錯誤は `experiments/NNN_<slug>/` の自己完結ディレクトリとして積み上げる。過去の実験は書き換えず、条件を変えるなら新しい番号で作る。
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

生データをリポジトリの外(外付けディスクや共有サーバー)に置く場合は `.env` の `HOST_DATA_DIR`、GPU を使うマシンでは `COMPOSE_FILE` を設定します(`.env.example` の説明を参照)。

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
├── experiments/           # 番号付き実験ディレクトリ(自己完結・試行錯誤の蓄積)
│   ├── README.md          # 実験の規約(AGENTS.md の Experiments の日本語版)
│   ├── _template/         # 新しい実験の雛形(summary.md・README.md・run.py・params.py・out/)
│   ├── EXP_SUMMARY.md     # 全実験の索引と状態(撤回を含む)
│   └── JOBS.md            # 長時間・高コストのジョブの台帳
├── tests/                 # pytest テストスイート
├── data/
│   ├── raw/               # 生データ(不変。Git には構造のみ)
│   ├── external/          # 外部から入手したデータ(不変。入手元は README.md の表に記録)
│   ├── interim/           # 中間生成データ
│   └── processed/         # 解析可能な派生データ
├── result/
│   ├── figures/           # 生成された図
│   ├── tables/            # 生成された表
│   └── animations/        # 生成されたアニメーション・動画
├── draft/                 # 原稿(LuaLaTeX。compile.sh でビルド、luatexja で日本語執筆可。tables/numbers.tex は生成物)
├── docs/                  # 人間向けドキュメント(研究ログ・意思決定記録)
├── .claude/               # Claude Code のスキルと設定(settings.json がホストでの python・uv の実行を拒否)
├── .agents/               # Codex のスキル(write-handoff は .claude/skills/ と同じ内容)
├── STATE.md               # 運用状態の単一ページ(セッション開始時に最初に読む)
├── AGENTS.md              # エージェント向け指示の正典(英語)
├── CLAUDE.md              # AGENTS.md への参照のみ(内容を書かない)
├── LICENSE                # MIT License
├── config.py              # 置き場所の定義だけ(ディレクトリとデータの場所)。結果を変えうる値は各実験の params.py
├── .env.example           # .env の雛形(UID/GID、HOST_DATA_DIR、GPU 用の COMPOSE_FILE)
├── Dockerfile
├── docker-compose.yml     # CPU のみのベース構成
├── docker-compose.gpu.yml # NVIDIA GPU 用オーバーライド
├── pyproject.toml
└── uv.lock                # コミット対象(uv add / remove 後に更新をコミット)
```

## 日常操作コマンド

### コンテナ操作

```bash
make help                                       # よく使う操作の一覧
docker compose build                            # 初回と、pyproject.toml・uv.lock を変えた後(make build)
docker compose up -d                            # 起動・設定変更後の再作成(make up)
docker compose down                             # 停止して削除(make down)
docker compose exec research-template bash      # コンテナに入る(必要な場合のみ。make shell)
```

コンテナは自動では再起動しません(再起動後は `make up`。`make` のテストなどは止まっていれば起動します)。ポートも公開しません。

### Python の実行とパッケージ管理

```bash
docker compose exec research-template uv run python scripts/<script>.py
docker compose exec research-template uv add <package>
```

`uv add` / `uv remove` の後は、`docker compose build` でイメージにも反映し、更新された `uv.lock` をコミットしてください。

ホストで `python`・`python3`・`pip`・`uv` を直接実行しません(`--version` も含む)。Claude Code では、コミットしてある `.claude/settings.json` がこれらを拒否します。Codex には同じ仕組みがないため、`AGENTS.md` の規則で守ります。

### テスト

```bash
make check                                      # ruff とすべてのテスト(コミット前に毎回)
docker compose exec research-template uv run pytest
```

テストは、解析の正しさを担保するもの(既知の答えを持つ合成データでの推定、単位・分母・丸めの独立計算との照合、再現手順の誤入力停止など)と、システム上の制約を守るものに絞ります。初めから入っているのは次のものです。

- `tests/test_config.py` — 置き場所の定義。`config.py` が場所(パス)だけを持ち、`DATA_ROOT` 以外の環境変数を読まないこと(共有の値を直して、完了した実験の結果が黙って変わるのを防ぐ)
- `tests/test_runtime_constraints.py` — Docker 内で動いていること、依存環境・キャッシュが作業ディレクトリの外にあること、生データが読み取り専用であること
- `tests/test_manuscript_structure.py` — 原稿の引用キー・参照ラベル・読み込むファイルと図が存在すること。章立て・語数・文言・主張は固定しません(文章は著者が確かめます)
- `tests/test_repo_structure.py` — 引き継ぎ用の文書があること、常に読む文書(STATE.md・索引・docs/guardrails.md)が字数の上限内で、索引の各行が短いこと、実験の名前と番号の重複、実験ディレクトリと `experiments/EXP_SUMMARY.md` の対応、各実験の `summary.md`(長さ・状態の語の一致・雛形の書き残し)、`out/` が Git に入らないこと、スキルを両方のエージェントが読み込めること
- `tests/test_experiment_harness.py` — 実験の雛形が動き、自分の `out/` だけに書くこと。smoke・上書き防止・昇格の規則
- `tests/test_new_experiment.py` — `make experiment` の番号・雛形の埋め込み・索引の行
- `tests/test_tex_numbers.py` — 原稿の数値の丸め(手計算との照合)、曖昧な値・行の拒否、コミットした `numbers.tex` が CSV と一致すること

### Jupyter(任意)

Jupyter は依存に含まれていません。使う場合は追加してから、必要なときだけ、このマシンからだけ見えるポートで起動します(ほかのプロジェクトとポートが重なったら 8889 を変える)。

```bash
docker compose exec research-template uv add jupyterlab
docker compose build
docker compose run --rm -p 127.0.0.1:8889:8888 research-template uv run jupyter lab --ip 0.0.0.0 --port 8888 --no-browser
```

ホスト側からは `http://localhost:8889` でアクセスします。

### 原稿(LuaLaTeX、ホストで実行)

```bash
bash draft/compile.sh            # draft/main.pdf と draft/supplementary.pdf(make tex でも可)
bash draft/compile.sh --review   # 行番号とダブルスペース入りの draft/main_review.pdf(make tex-review)
```

`compile.sh` は `lualatex` → `bibtex`(参考文献を宣言し、引用がある文書だけ) → `lualatex` → `lualatex` を `main.tex` と `supplementary.tex` に対して実行し、中間ファイルはすべて Git 管理外の `draft/build/` に書いて、PDF だけを `draft/` に残します。画面にはエラー(ファイル名と行番号)だけを出し、記録は `draft/build/<文書名>.log` に残します。未定義の引用や参照が残っていると、PDF を書いたうえで 0 以外で終わります。`draft/` の中で `lualatex` を手で実行しないでください。そこに残った古い `.aux`・`.bbl` が次のビルドで黙って読まれ、参考文献や参照が欠けた PDF ができます。

査読用の版(`--review`)は本文が同じで、`main.tex` の `\ifdefined\reviewformat` が書式だけを切り替えます。投稿時に行番号を求める誌が多いため用意しています。

原稿の数値と表は手で書かず、`result/tables/` の CSV からコードで LaTeX のマクロや表のファイルを書き出して `\input` します(CSV の検査が通っても、手で書き写した数値は古いまま残るため)。本文の数値は `scripts/make_numbers.py` に1つずつ登録し(どの CSV のどの行・列を、どう丸めるか)、`make numbers` で `draft/tables/numbers.tex` のマクロにして、本文では `\Name{}` と書きます。丸めは10進の四捨五入で、ちょうど半分の値や見つからない行は止まります。CSV を直したら `make paper`(数値の生成と PDF の作成)を実行し、`numbers.tex` も CSV と一緒にコミットします(古いままだとテストが落ちます)。`result/tables/` の CSV はコミットします。

コードで `result/figures/` へ昇格した図は、原稿がそこから直接読みます(`\graphicspath`)。`draft/figures/` には手で作った図(模式図など)だけを置きます。

`draft/main.tex`・`draft/supplementary.tex` は見出しのみの雛形です。luatexja + 原ノ味フォントを読み込んでおり、日本語でも執筆できます。

### GPU(任意)

ベース構成は CPU のみです。NVIDIA GPU を使うマシンでは、`.env` に次の1行を書きます。以後の `docker compose` はすべて GPU 込みの構成で動きます。

```bash
COMPOSE_FILE=docker-compose.yml:docker-compose.gpu.yml
```

`-f docker-compose.gpu.yml` を1回だけ付けて起動すると、次に `docker compose up -d`(`uv add` の後など)を実行したとき、GPU のないコンテナに黙って作り直されます。

## 実験の回し方

試行錯誤の実験は `experiments/` 以下に番号付きディレクトリとして蓄積します。各実験には、今の結論を短くまとめた `summary.md` と、経緯の記録 `README.md` を置きます。手順・状態の語・撤回のしかたは [`experiments/README.md`](experiments/README.md) にあります。

```bash
make experiment SLUG=<slug>   # 番号を決め、雛形を複製し、索引に「進行中」の行を足す
docker compose exec research-template uv run python experiments/NNN_<slug>/run.py --smoke   # 小さく通す
docker compose exec research-template uv run python experiments/NNN_<slug>/run.py           # 本実行
```

出力はすべて各実験の `out/` に入り(Git 管理外)、`out/params_used.json` に状態・シード・パラメータ・コミットと未コミットのファイルの一覧・各段の所要時間が残ります。原稿や後の実験が使う表・図は、コード(`run.promote()`)で `result/` へ昇格させます。

## データの扱い

- **コンテナ内**では、`docker-compose.yml` が `./data/raw`(`.env` の `HOST_DATA_DIR` を設定すればそのディレクトリ)を `/data` に**読み取り専用**でマウントし、常に `DATA_ROOT=/data` を設定します。コードは `config.RAW_DATA_DIR` から読みます。同じデータは作業ディレクトリ経由(`/workspace/data/raw`)でも見えるため、そこにも読み取り専用で重ね、どちらの経路からも書き換えられないようにしています。
- 入力データは `data/raw/` に置きます。大容量ファイル(`.nc`, `.h5`, `.parquet` など)は `.gitignore` 済みで、Git には入りません。
- 第三者が作ったデータ(公開データセット、共同研究者から受け取ったデータ、参照用のカタログなど)は `data/external/` に、入手したままの形で置きます。コードからは `config.EXTERNAL_DATA_DIR` で読みます。手で編集せず、加工したものは `data/interim/`・`data/processed/` に出します。データセットごとの入手元(URL か DOI、版、入手日、ライセンス)を [`data/external/README.md`](data/external/README.md) の表に記録します。中身は Git に入りません(コミットされるのはその README だけです)。コンテナ内では読み取り専用にしていないので、ダウンロード用のスクリプトがここへ書き込めます。

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
| `STATE.md` | 日本語 | 運用状態の単一ページ(フェーズ、実行中のジョブ、決定、次の作業) | 状態が変わったらその場で。結果・決定・ジョブ・次の作業を変えたタスクの完了を報告する前と長時間ジョブの投入前は `write-handoff` スキルで更新してコミットする。字数の上限はテストが検査する |
| `experiments/EXP_SUMMARY.md` | 日本語 | 全実験の索引と状態(撤回を含む) | 実験の作成時に1行足し、状態や結論が変わったら直す。状態の語は `summary.md` と同じにする。1行は短く、字数の上限はテストが検査する |
| `docs/guardrails.md` | 日本語 | 撤回した主張と、繰り返さない失敗(1件1行) | 起きたらその場で。毎セッション読むので字数の上限をテストが検査する |
| `docs/` | 日本語 | 研究ログ・意思決定記録など人間向け文書の蓄積場所 | 随時追記。使い方は [`docs/README.md`](docs/README.md) |
| `experiments/README.md` | 日本語 | 実験の規約(`AGENTS.md` の Experiments の日本語版) | 実験の規約を変えたら `AGENTS.md` と同じ編集で直す |
| `experiments/*/summary.md` | 日本語 | その実験の今の結論(状態・答え・言えないこと・主な数値と出所) | 作成時に問いと判定の規則、本実行の後に答え。結論が変わったら書き直す |
| `experiments/*/README.md` | 日本語 | その実験の経緯の記録(目的・方法・結果・考察・訂正) | 意味のある実行のたびに日付をつけて追記する。古い記述は消さない |

各情報の正は1箇所だけにし、同じ表を複数のファイルに持ちません(対応表は `AGENTS.md` の Single Source of Truth)。チャットの内容は、次のセッションにも、もう一方のエージェントにも引き継がれません。残す価値のある情報は、その場でファイルに書きます。

**更新のトリガー:**

- ディレクトリ構成・実行環境・ワークフロールールを変えたら、`README.md` と `AGENTS.md` をセットで更新する(片方だけ直して不整合を残さない)。実験の規約は `AGENTS.md` の Experiments と `experiments/README.md` をセットで直す。
- 「なぜそうしたか」という判断や経緯は `docs/` に記録する。雛形は [`docs/templates/`](docs/templates/) にあります。
- 結論を撤回・訂正・置き換えしたら、`experiments/README.md` の手順で、同じコミットに反映する。
- 日本語の文書では、日本語で自然に書ける一般語を不必要に英語で書かない(コードの識別子と正式名称は除く)。日本語と英語が頻繁に混ざる文体を避ける。

## ライセンス

このリポジトリに含まれるコード、設定ファイル、文書・原稿の雛形は [MIT License](LICENSE) で公開しています。

このテンプレートから作成した研究リポジトリに後から追加される研究データ、個別の論文原稿、図表、第三者由来の素材へ MIT License が自動的に適用されるわけではありません。それぞれの権利者、データ提供元、共同研究契約、倫理審査、投稿規程に従って、公開範囲とライセンスを個別に定めてください。

## エージェントのスキル

Claude Code は `.claude/skills/`、Codex は `.agents/skills/` からスキルを読み込みます。どちらも先頭に YAML の見出し(`name`・`description`)が要ります。見出しの無いスキルを Codex は読み込みません。

- **`write-handoff`**(Claude Code・Codex) — 結果・決定・ジョブ・次の作業を変えたタスクの完了を報告する前や、長時間ジョブの投入前に `STATE.md` を更新してコミットし、次のセッションが `STATE.md` を入口にファイルだけで再開できる状態にします。2つのディレクトリに同じ内容で置きます(テストが一致を検査します)。

エージェントのメモリ(Claude Code の自動メモリ、Codex のメモリ)は道具ごと・マシンごとで、もう一方のエージェントからは読めません。研究の状態・結果・決定はメモリに置かず、上の文書に書きます。
