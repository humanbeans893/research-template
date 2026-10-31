# エージェントの実行記録（Claude Code と Codex で共有）

Claude Code と Codex は、それぞれ別の場所に記録を持つ（Claude Code は `~/.claude/projects/`、
Codex は `~/.codex/sessions/`）。ワークフローの作業領域は `/tmp` のセッション専用の場所にあり、
別のセッションや別のアカウント、もう一方のエージェントからは見えず、再起動で消える。
この `.agent-runs/` は、両方のエージェントが同じ実行記録を読み書きするための、消えない置き場所である。
運用の全体は、リポジトリ直下の `DYNAMIC_WORKFLOW.md` にある。

git では、この `README.md` と `shared/tools/` だけを追跡する。それ以外（記録そのもの）は会話の全文への
参照を含むので、管理外に置き、外へ出さない。

## 構成

| 場所 | 中身 |
|---|---|
| `sessions.jsonl` | このリポジトリと作業ツリーで動いた両エージェントのセッションの一覧 |
| `prefixes.txt` | 任意。追加の対象ディレクトリを1行に1つ。末尾が `*` の行だけ文字列の接頭辞として扱う（例：`/tmp/ks-*`） |
| `runs/<run>/` | ワークフロー1回分の台本、設定、実行記録、結果、段階ごとの状態 |
| `runs/<run>/stages/<key>-<role>/` | 各段階の作業ディレクトリ。Codex の段階は `<key>-cx-<role>/` |
| `notes/` | セッションのメモと、ワークフローの見積もり・実測の記録（`YYYYMMDD_topic.md`） |
| `shared/` | 段階をまたいで使う入力（Codex に渡す共通の計画と規則、出力のスキーマ、仕様など）と `tools/` |

`sessions.jsonl` にはエンジン、ID、作業ディレクトリ、開始と終了、最初の依頼、記録の場所を保存する。
`shared/tools/index_sessions.py` で作り直す。リポジトリ自体と git の作業ツリーは自動で含まれる。
`prefixes.txt` と `--prefix` は通常、そのディレクトリ自身と配下だけに一致する。
`/x/repo` は `/x/repo-other` に一致しない。末尾の `*` を使えば `/tmp/ks-*` で `/tmp/ks-a` などをまとめられる。

`runs/<run>/` には `manifest.json`（ID、引数、続きの地点）、`script.js`（台本）、`journal.jsonl`（写し）、
`results.json`（段階ごとの最新の結果）、`stages.jsonl`（状態、記録の場所、入力換算の使用量、Codex の
セッションと週の枠の使用率）を保存する。Codex の段階の作業ディレクトリには `prompt.md`（指示）、
`events.jsonl`（出来事）、`last.json`（最終報告）、`stderr.txt`、`scratch/` を置く。

## 読み方（セッションの始め、または引き継ぎのとき）

1. 運用の状態の文書（`STATE.md` など）を読む。
2. `sessions.jsonl` の末尾で、直近にどちらのエージェントが何をしていたかを見る。
3. 実行中または直前のワークフローの `runs/<run>/manifest.json`、`results.json`、`stages.jsonl` を読む。
   途中で止まった段階は `status` が `failed` か、`stages.jsonl` に無い。その段階の記録（Claude Code は
   `transcript`、Codex は `codex[].codex_transcript`）の末尾で、どこまで進んだかを確かめる。

## 書き方

- ワークフローの台本は、段階の作業ディレクトリを `runs/<run>/stages/` に置く。`/tmp` のセッション専用の
  作業領域には置かない。起動したら `runs/<run>/manifest.json` にワークフローの ID と引数を書く。
- ワークフローが終わったとき、止めたとき、利用上限で落ちたときは、記録を書き出す。
- セッションを始めたとき、終えるときに、セッションの一覧を作り直す。

## 道具（`shared/tools/`、標準ライブラリだけ、記録を読むだけ）

| 道具 | 用途 |
|---|---|
| `index_sessions.py` | 両エージェントのセッションの一覧（`sessions.jsonl`）を作る |
| `export_workflow_run.py <journal.jsonl> --run <名前> --script <台本>` | ワークフローの1回の実行を `runs/<名前>/` に書き出す |
| `token_units.py <transcript>...` | 作業者の記録の使用量を入力換算で足す |
| `tail_agent.py <transcript> [件数]` | Claude Code の作業者の記録の末尾を読む |

ホストで Python を動かしてよいリポジトリでは、そのまま `python3 .agent-runs/shared/tools/<道具>` で動かす。
ホストで Python を動かさない決まりのリポジトリでは、使い捨てのコンテナで、記録の置き場所をホストと同じ
パスに読み取り専用でつないで動かす（ネットワークは使わない。イメージは Python の入った任意のもの）。

```bash
docker run --rm --network none -u "$(id -u):$(id -g)" -e HOME="$HOME" -w "$PWD" \
  -v "$PWD:$PWD" \
  -v "$HOME/.claude/projects:$HOME/.claude/projects:ro" \
  -v "$HOME/.codex/sessions:$HOME/.codex/sessions:ro" \
  <python-image> python3 .agent-runs/shared/tools/index_sessions.py
```
