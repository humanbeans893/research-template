# research-template

データ解析・図表生成・原稿執筆までを 1 つのリポジトリで完結させるための、研究プロジェクト用テンプレートです。

- この **README.md は人間向けの入口ドキュメント(日本語)** です。
- コーディングエージェント(Claude Code / Codex CLI など)向けの指示は **`AGENTS.md`(英語)が正典**です。詳細は「[文書整備の方針](#文書整備の方針)」を参照してください。

## このテンプレートの目的と研究方針

新しい研究を、再現可能な形で素早く始めるための共通土台です。このテンプレートから作られたプロジェクトでは、次の方針を守ります。

1. **再現性第一** — すべての結果(図・表・数値)は、コードから再生成できる状態を保つ。
2. **`data/raw/` は不変(イミュータブル)** — 生データは手で編集しない。Git には構造のみ残し、大容量ファイルはコミットしない。
3. **派生データは再生成する** — `data/interim/`・`data/processed/` はスクリプトの出力。直接編集せず、必要ならコードを直して再生成する。
4. **再利用コードは `src/`、スクリプトは薄く** — 共有ロジックは `src/` に置き、`scripts/` は再利用関数を呼び出すだけのエントリポイントにする。
5. **`result/` は生成物** — 図表は手で編集せず、コードから再生成する。
6. **実行環境は Docker + uv に統一** — ホストの Python や `.venv` には依存しない。
7. **原稿のみホストの LuaLaTeX** — `draft/` 以下のコンパイルはコンテナではなくホストで行う。

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

### 3. 環境変数を設定する

```bash
cp .env.example .env
id -u; id -g   # 出力に合わせて .env の UID / GID を設定
```

他のプロジェクトとポートが衝突する場合は、`.env` で `HOST_JUPYTER_PORT` を変更してください(既定 8889)。

### 4. コンテナを起動し、依存を同期する

```bash
docker compose up -d
docker compose exec research-template uv sync
```

依存パッケージは**イメージのビルド時ではなく実行時に同期**されます(`.venv` はマウントされた作業ディレクトリ内に作られます)。

### 5. 動作確認

```bash
docker compose exec research-template uv run pytest
```

`tests/test_config.py` が通れば環境構築は完了です。

### 6. 最初のコミット

リネームした一式と、`uv sync` で更新された `uv.lock` をコミットします。

## ディレクトリ構成

```text
research-template/
├── src/                   # 再利用可能なソースコード
│   ├── utils/             # 汎用ユーティリティ(パス・数学・描画・検証・乱数・I/O)
│   ├── models/            # ドメインオブジェクト・データコンテナ・ローダ・パーサ
│   ├── methods/           # 解析手法・統計処理・アルゴリズム・モデリング
│   └── analysis/          # 上記を組み合わせた高次の解析ワークフロー
├── scripts/               # 実行用エントリポイント(ロジックは持たせない)
├── tests/                 # pytest テストスイート
├── data/
│   ├── raw/               # 生データ(不変。Git には構造のみ)
│   ├── interim/           # 中間生成データ
│   └── processed/         # 解析可能な派生データ
├── result/
│   ├── figures/           # 生成された図
│   ├── tables/            # 生成された表
│   └── animations/        # 生成されたアニメーション・動画
├── draft/                 # 原稿(LuaLaTeX。luatexja で日本語執筆可)
├── docs/                  # 人間向けドキュメント(研究ログ・意思決定記録)
├── .claude/               # Claude Code のスキルと補助スクリプト
├── AGENTS.md              # エージェント向け指示の正典(英語)
├── CLAUDE.md              # AGENTS.md への参照のみ(内容を書かない)
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

`uv add` / `uv remove` の後は、更新された `uv.lock` をコミットしてください。

### テスト

```bash
docker compose exec research-template uv run pytest
```

### Jupyter(任意)

Jupyter は依存に含まれていません。使う場合は追加してから起動します。

```bash
docker compose exec research-template uv add jupyterlab
docker compose exec research-template uv run jupyter lab --ip 0.0.0.0 --port 8888 --no-browser
```

ホスト側からは `http://localhost:8889`(`.env` の `HOST_JUPYTER_PORT` で変更可)でアクセスします。

### 原稿(LuaLaTeX、ホストで実行)

```bash
cd draft && lualatex -interaction=nonstopmode main.tex
```

参考文献を更新した場合はフルシーケンスで:

```bash
cd draft
lualatex -interaction=nonstopmode main.tex
bibtex main
lualatex -interaction=nonstopmode main.tex
lualatex -interaction=nonstopmode main.tex
```

`draft/main.tex`・`draft/supplementary.tex` は見出しのみの雛形です。luatexja + 原ノ味フォントを読み込んでおり、日本語でも執筆できます。

### GPU(任意)

ベース構成は CPU のみです。NVIDIA GPU を使うマシンでは:

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
```

## データの扱い

- **コンテナ内**では、`docker-compose.yml` が `./data/raw` を `/data` に**読み取り専用**でマウントし、常に `DATA_ROOT=/data` を設定します。
- **ホスト側**で `config.py` を使う場合は、`.env` の `DATA_ROOT`、未設定なら `./data/raw` にフォールバックします。
- 入力データは `data/raw/` に置きます。大容量ファイル(`.nc`, `.h5`, `.parquet` など)は `.gitignore` 済みで、Git には入りません。

## 文書整備の方針

このテンプレートでは、文書の役割を次のとおり分離します。

| ファイル | 言語 | 役割 | 更新ルール |
|---|---|---|---|
| `README.md` | 日本語 | 人間向けの入口(方針・手順・コマンド) | 構成やワークフローの変更時に `AGENTS.md` と**同時に**更新する |
| `AGENTS.md` | 英語 | エージェント向け指示の**正典** | 運用ルールの変更は必ずここに書く |
| `CLAUDE.md` | — | `See @AGENTS.md` の**ポインタのみ** | **内容を追加しない**。編集は常に `AGENTS.md` へ |
| `docs/` | 日本語 | 研究ログ・意思決定記録など人間向け文書の蓄積場所 | 随時追記。使い方は [`docs/README.md`](docs/README.md) |

**更新のトリガー:**

- ディレクトリ構成・実行環境・ワークフロールールを変えたら、`README.md` と `AGENTS.md` をセットで更新する(片方だけ直して不整合を残さない)。
- 「なぜそうしたか」という判断や経緯は `docs/` に記録する。雛形は [`docs/templates/`](docs/templates/) にあります。

## Claude Code スキル

- **`/session-save`** — セッションでの作業内容をメモリと `.claude/sessions/` 以下の Markdown ログに保存します。
- **`/zotero-connect`** — WSL2 から Windows 上の Zotero へのポートフォワードを開始します(`.claude/scripts/zotero-forward.py`)。詳細は `AGENTS.md` の Zotero MCP 節を参照してください。
