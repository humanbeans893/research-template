# 動的ワークフローの運用手引き

Claude Code の動的ワークフロー（`Workflow` で多数の作業者を動かす仕組み）と Codex を組み合わせ、
大きな作業を利用上限の中で確実に進めるための運用方法をまとめる。特定のリポジトリに依存しない形で
書いてあり、他のリポジトリでもそのまま使える。数値の例は、ある研究リポジトリでの作業
（2026-10-16〜17、Claude Max と Codex prolite）での実測で、毎回測り直す前提の参考値である。

---

## 1. 原則

1. **起動の前に見積もる。** 作業者の数、1体あたりの使用量、総量、利用上限の残りから同時実行数を
   決める。固定の数や推測で決めない。
2. **記録は消えない共有の場所に置く。** `/tmp` のセッション専用の作業領域や、エンジンごとの
   キャッシュだけに置かない。Claude Code と Codex の両方が同じ記録を読み書きする。
3. **書く作業と確かめる作業を別のエンジンに分ける。** Codex が書き、Opus がレビューと最終確認をする。
4. **作業者はローカルにコミットするだけ。** push、PR、マージ、外部への書き込みは主セッションが、
   そのセッションで得た利用者の承認のもとで行う。
5. **失敗した作業者の後続は起動しない。** 止まった実行は、記録から続きの地点を指定して新しく起動する。
6. **主セッションは監督に徹する。** 主セッションは文脈が大きく、1回の操作が重い。実行中は操作を控える。

---

## 2. 起動前の見積もり

1. 台本が起動する作業者を、項目と段階（実装、観点ごとのレビュー、修正、最終確認、見込まれる
   やり直し）ごとに数える。
2. 段階ごとの1体あたりの使用量を、同じ種類の段階の実測から見積もる。単位は入力換算とする。

   ```
   入力換算 = 入力 + 1.25 × キャッシュ書込み + 0.1 × キャッシュ読出し + 5 × 出力
   ```

   作業者の記録 `~/.claude/projects/<project>/<session>/subagents/workflows/<run>/agent-*.jsonl` の
   `message.usage` を、メッセージの id ごとに一度だけ足す（6章の `token_units.py`）。作業者の記録では
   出力トークンが少なく記録されるが、較正は同じ数え方の比なので、そのまま使える。
   同じ種類の実測が無い段階は、1〜2体だけ先に走らせて測る（試験運用）。
3. 較正する。`get_usage` の5時間枠と週の枠の使用率の増分と、同じ時間のこのセッション（主セッションと
   作業者）の入力換算の増分から、1%あたりの入力換算を求める。目盛りは1%なので、10〜15分以上あけて測る。
   `get_usage` が `unavailable` や `not_applicable` を返す、または増分が読めないときは、1体だけ10〜15分
   走らせて測る。それでも測れなければ、起動の前に利用者に確かめる。
4. 総量を、5時間枠の何枠分か、週の枠の何%かに換算する。週の枠の大部分を使う、または残りを超える
   見込みなら、対象と深さ（項目、レビューの観点の数）を利用者と決めてから起動する。
5. Codex を使うときは、Codex の週の枠の残り（7章）も同じように見積もる。

---

## 3. 同時実行数

```
c = floor( (5時間枠の残り% − 主セッションの余裕%) ÷ (1体の毎時%) ÷ (再設定までの時間) )
```

- 種類ごと（Opus の作業者、Codex を待つ薄い作業者、Codex 本体）に分けて計算する。Codex 本体は
  Claude の枠ではなく Codex の週の枠で決める。
- `c = 0` なら起動しない（再設定を待つか、対象を減らす）。台本は 0 を「その種類の段階を止めて待つ」
  として扱えるようにしておく。
- 使用量が枠で決まる限り、`c` を上げても一つの枠でできる作業の量は増えない。上げすぎると枠を早く
  使い切り、上限に達した時点で実行中の作業者の途中の作業が失われ、再設定まで何もできない。
- 起動の10〜15分後に使用率を測り直す。ずれていれば止めて、記録から新しい実行として続ける（5章）。

---

## 4. エンジンとモデルの分担

| 段階 | エンジン | モデルと推論の強さ |
|---|---|---|
| rebase、レビュー指摘の修正、小さな仕上げ | Codex | 主力のモデル（例：gpt-6.1-sol）の xhigh |
| 通常の実装 | Codex | 主力のモデルの max |
| 難所（規則や仕様からの新規実装、ビット単位の一致が要る高速化、大きな途中の実装、2回目の修正） | Codex | 最上位のモデル（例：gpt-6-astra）の max |
| 観点ごとのレビュー、最終確認、仕様のレビュー | Claude | Opus |
| Codex を起動して終わるまで待つだけの薄い作業者 | Claude | Sonnet、推論は low |

- ultra（Codex 自身が作業をさらに分ける段階）は、作業ツリーの規律と記録が崩れるので使わない。
- **薄い作業者**（付録 A）は、指示をファイルに書き、Codex を背景で起動し、終わるまで待ち、
  `--output-schema` で決めた形の最終報告をそのまま返すだけにする。リポジトリを読んだり直したりしない。
- **サンドボックス：** Codex の標準のサンドボックス（workspace-write）は、Docker への接続、`.git` への
  書き込み（`--add-dir` で加えても読み取り専用）、ネットワークを拒否する。試験とコミットは
  `--approve-for-me`（Codex の自動審査）で通す。段階の作業ディレクトリは `--add-dir` で書けるようにする。
- **権限：** Claude Code の自動判定は、自動承認つきの起動を止める。`.claude/settings.local.json` に
  `Bash(codex exec --approve-for-me:*)` の許可を置き、コマンドは必ず `codex exec --approve-for-me` で
  始める（前に `timeout` や `cd` を付けると許可の規則に合わない）。
- **新しいブランチ：** Codex を起動する前に作業ツリーを作る。存在しないディレクトリでは Codex が始まらない。
- **指示：** 共通の計画と規則は一つのファイル（`common.md`）にして参照させ、段階ごとの指示は短くする。
  「最終報告はスキーマどおりの JSON だけ」と書く。Codex は作業ツリーの `AGENTS.md` を自分で読む。

---

## 5. 台本の設計

- **項目ごとの鎖：** 実装（または前回の続き）→ 観点ごとのレビュー → 修正 → 最終確認 →
  確認が通らなければ修正のやり直し（最大2回、2回目は上位のモデル）。依存する項目は親の完了で始める。
- **失敗の扱い：** 記録の明示的な失敗、結果が null、報告の `codex_status` が `failed` で始まる場合は、
  その項目の鎖を止める。空の結果で確認の作業者を起動しない。上限に達したとき、待ち行列の作業者が
  次々に起動して即座に失敗するのを防ぐ。
- **同時実行：** 優先度つきの共有の枠で同時実行数を守り、臨界経路を最優先にする。仕様のレビューの
  ように後の段階の前提になる作業も最優先にする（低くすると回らず、後の段階が待たされる）。
- **大きな結果は参照で渡す：** 前の段階の報告をプロンプトに埋め込まず、記録のファイルとキーで参照
  させる（`jq '.["<key>"]' results.json`）。
- **再開：** `resumeFromRunId` が完了分を再利用するのは、同じ台本・同じ引数・同じ呼び出しの順序の
  ときだけである。空き枠で起動の時期が決まる台本では順序が毎回変わるので、実質的に再利用されない。
  止めたら、ブランチごとの続きの地点（次に回す段階と、記録の中の直前の報告のキー）を書いた後継の
  台本を、新しい実行として起動する（付録 B）。引数を変えて同じ実行を再開しない。
- **作業ディレクトリ：** 段階の作業ディレクトリ（指示、出来事の記録、最終報告）は共有の記録の
  `runs/<run>/stages/` に置く。
- **決定性：** 時刻や乱数をプロンプトに入れない。
- **途中の作業：** 各段階の指示に、前の試みが残した未コミットの作業や途中の操作（rebase など）の
  扱いを書く（「まず git status と git log を見て、残っている作業を確かめてから続ける」）。

---

## 6. 共有の実行記録

リポジトリ直下の `.agent-runs/` に置く。読み方と道具の使い方は `.agent-runs/README.md` にある。

| 場所 | 中身 |
|---|---|
| `README.md` | 読み方と書き方 |
| `sessions.jsonl` | 両エージェントのセッションの一覧（エンジン、ID、作業ディレクトリ、開始と終了、最初の依頼、記録の場所） |
| `runs/<run>/` | 実行ごとの台本、設定、実行記録、段階ごとの最新の結果と状態（詳細は `.agent-runs/README.md`） |
| `runs/<run>/stages/<key>-<role>/` | 段階の作業ディレクトリ。Codex の段階のファイルは `.agent-runs/README.md` を参照 |
| `shared/` | 段階をまたぐ入力（`codex/common.md`、出力のスキーマ、試験用の補助、仕様、前の実行の結果）と `tools/` |
| `notes/` | セッションのメモと、見積もり・実測の記録 |

- **読む：** セッションの始めと引き継ぎで、運用の状態の文書（`STATE.md` など）→ `README.md` →
  `sessions.jsonl` の末尾 → 直前の `runs/<run>/results.json` と `stages.jsonl`。
- **書く：** ワークフローが終わった、止めた、上限で落ちたら `export_workflow_run.py`。
  セッションの始めと終わりに `index_sessions.py`。
  書き出しでは壊れた行を飛ばし、失敗した段階にも Codex の情報を残す。段階の場所は報告中の
  `stage <dir>;` から読み、無ければ `--stages-dir` で指定した場所から探す。
- **git：** 記録は会話の全文への参照を含むので管理外にし、`README.md` と `shared/tools/` だけを追跡する。
- **道具**（`shared/tools/`、標準ライブラリだけ、記録を読むだけ）：
  - `token_units.py`：作業者の記録の使用量を入力換算で足す。
  - `export_workflow_run.py`：ワークフローの実行を `runs/<run>/` に書き出す。
  - `index_sessions.py`：両エージェントのセッションの一覧を作る。
  - `tail_agent.py`：作業者の記録の末尾を読む。
- **ホストで Python を動かさない決まりのリポジトリ：** 道具は使い捨てのコンテナで、記録の置き場所を
  ホストと同じパスに読み取り専用でつないで動かす（コマンドは `.agent-runs/README.md`）。
- **新しいリポジトリで使うとき：** `DYNAMIC_WORKFLOW.md`、`.agent-runs/README.md`、`.agent-runs/shared/tools/` を
  写し、`.gitignore` に次を加え、`AGENTS.md` にこの手引きと記録の読み書きの決まりを書く。`/tmp` の作業ツリーや
  関連するリポジトリもこのリポジトリの作業とみなすなら、`.agent-runs/prefixes.txt` に対象ディレクトリを書く。
  リポジトリ自体と git の作業ツリーは自動で含まれる。通常はその場所と配下だけを対象とし、末尾が `*` なら
  文字列の接頭辞として扱う（例：`/tmp/ks-*`）。`index_sessions.py --prefix` も同じ指定方法である。

  ```gitignore
  .agent-runs/*
  !.agent-runs/README.md
  !.agent-runs/shared/
  .agent-runs/shared/*
  !.agent-runs/shared/tools/
  .agent-runs/shared/tools/__pycache__/
  ```

---

## 7. 使用量の監視

- **Claude：** `get_usage` の5時間枠と週の枠の使用率と再設定の時刻。
- **Codex：** セッションの記録 `~/.codex/sessions/**/rollout-*.jsonl` の `token_count` の
  `rate_limits.primary` と `rate_limits.secondary` のうち、`window_minutes == 10080` の枠の
  `used_percent` と `credits` を読む。書き出した段階の記録には `weekly_percent_first_last` と
  `window_minutes` が並ぶ。週の観測が無ければ両方 null になる。手元の記録に無い消費（GitHub での Codex の
  PR レビュー、別の端末、クラウドの作業）でも減るので、起動の前と各段階の後に読む。
- **クレジット：** 上限を超えてクレジットを使うのは、利用者の承認があるときだけ。クレジットの残高が
  あると上限の後に自動で使われるおそれがあるので、承認が無ければ Codex の段階を止める（同時実行数 0）。

---

## 8. 上限に達したとき

- **Claude の上限：** 実行中の作業者（Codex を待つ薄い作業者を含む）が失敗し、その背景の Codex も
  止まる。完了分は記録にある。再設定の後、記録から続きの地点で新しい実行を起動する。
- **Codex の上限：** Codex の段階が失敗する。クレジットの承認が無ければ、Codex の段階を止めて Opus の
  確認だけを進めるか、書く段階を Opus に切り替える（見積もりをやり直す）。
- **止めたあとの確認：** 作業ツリーに途中の rebase や未コミットの変更が無いか、残った Codex の処理や
  試験用のコンテナが無いかを確かめる。止めるのは自分が起動したものだけにする。

---

## 9. チェックリスト

**起動の前**
- [ ] 作業者の数と段階ごとの使用量を見積もり、総量を5時間枠と週の枠に換算した
- [ ] Claude と Codex の使用率を読み、同時実行数を種類ごとに計算した（0 なら起動しない）
- [ ] 週の枠の大部分を使うなら、対象と深さを利用者と決めた
- [ ] 段階の作業ディレクトリと入力は共有の記録にある（`/tmp` だけではない）
- [ ] 新しいブランチの作業ツリーを作る手順が、Codex の起動より前にある
- [ ] 作業者は push、PR、マージをしない。外部への書き込みは主セッションだけ
- [ ] `manifest.json` に、ワークフローの ID、引数、続きの地点を書いた

**起動の後**
- [ ] 10〜15分後に使用率を測り直した
- [ ] 実行中は主セッションの操作を控えている

**終わった、止めた、落ちたとき**
- [ ] `export_workflow_run.py` で記録を書き、ブランチごとの到達点を確かめた
- [ ] 残った Codex の処理、コンテナ、途中の rebase、未コミットの変更が無い
- [ ] 運用の状態の文書（`STATE.md` など）を更新した
- [ ] 続けるときは、続きの地点を書いた新しい実行として起動した（引数を変えた再開をしない）

---

## 10. 参考の実測値（2026-10-16〜17）

| 項目 | 値 |
|---|---|
| Claude の5時間枠の1% | 入力換算 約 0.47M（Max プラン） |
| Opus の重い作業者1体 | 毎時 6.6〜7.6M、5時間枠の毎時 約15%（夜間の Opus 1体と薄い作業者2体の実測では合計で毎時 約10%） |
| Opus の1段階 | rebase 約 1.0M、レビュー 約 2.2M、修正 約 2.4M、仕様の初版 約 6M |
| Opus 2体と薄い作業者2体 | 5時間枠の毎時 約26% |
| Codex を待つ薄い作業者（Sonnet） | 1段階 約 0.23M（Opus の修正の約1/10） |
| Codex の1段階 | 4〜10M トークン（大半はキャッシュ）、週の枠の0〜4%（xhigh〜max）、所要 20分〜1時間 |
| Codex の自動審査 | 1段階 約 1M トークン |

---

## 11. 失敗の記録（繰り返さない）

| 何が起きたか | 教訓 |
|---|---|
| 10体の同時実行で5時間枠を1時間足らずで使い切り、90体中66体が失敗した。大半は上限の後に起動して最初の要求で失敗した | 起動前に見積もる。失敗の後続を起動しない |
| xhigh の試験では週の増分が1%未満に見えたが、max は1〜4%。手元以外の消費でも一晩に約58%減った | 数値を一般化せず、段階の種類ごとに測り、各段階の後に使用率を読む |
| 同時実行数を変えた再開でも、同じ引数の再開でも、完了済みの段階がやり直しになりかけた | 再開のキャッシュに頼らず、続きの地点を書いた新しい実行で続ける |
| 作業ツリーを作る前に Codex を起動し、実装が始まらなかった | 作業ツリーを先に作る |
| 仕様のレビューを低い優先度にして回らず、それを前提にする実装が待たされた | 前提になる作業を最優先にする |
| 記録を `/tmp` のセッション専用の領域や、別の目的のディレクトリに置いた | 共有の実行記録に置く |
| Claude Code の自動判定が、承認の無いマージや自動承認つきの起動を止めた。別のセッションの承認は引き継がれなかった | 承認はそのセッションでもらう。恒常的な許可は権限の設定に置く |
| 返信のコメントを場所の照合の誤りで全部同じ文にした | 一括の操作の結果をすぐ確かめる |

---

## 付録 A：Codex の段階を待つ薄い作業者（雛形）

```js
function codexStage({ key, role, worktree, model, effort, body, label, phase, setup }) {
  const dir = `${LEDGER}/runs/${RUN}/stages/${key}-cx-${role}`
  const prompt = `Read ${COMMON} first.\n\nSTAGE DIRECTORY: ${dir}/scratch/\n\n${body}`
  return CODEX_POOL(priority(key), () => agent(`You are a thin wrapper that runs ONE Codex stage and returns its report.
Do not read, edit, test or commit anything yourself.
STEPS
${setup ? `0. ${setup}\n` : ''}1. mkdir -p ${dir}/scratch/
Write the text between <<<PROMPT and PROMPT>>> to ${dir}/prompt.md exactly.
2. Start Codex with exactly this single Bash command, with the Bash tool's run_in_background option:
codex exec --approve-for-me -C ${worktree} --add-dir ${dir} -m ${model} \\
  -c model_reasoning_effort='"${effort}"' --json --output-schema ${SCHEMA} \\
  -o ${dir}/last.json - < ${dir}/prompt.md > ${dir}/events.jsonl 2> ${dir}/stderr.txt
3. Repeat this foreground command (Bash timeout 600000) until it prints CODEX_EXITED:
p=$(pgrep -nf '[c]odex exec --approve-for-me -C ${worktree} ')
if [ -z "$p" ]; then
  echo CODEX_EXITED
else
  timeout 590 tail --pid=$p -f /dev/null
  if kill -0 $p 2>/dev/null; then echo STILL_RUNNING; else echo CODEX_EXITED; fi
fi
4. cat ${dir}/last.json; tail -n 5 ${dir}/stderr.txt; grep '"turn.completed"' ${dir}/events.jsonl | tail -n 1
5. Return every field of last.json unchanged and codex_status = "ok: stage ${dir}; <usage line>"
or "failed: stage ${dir}; <stderr tail>".
<<<PROMPT
${prompt}
PROMPT>>>`, { label, phase, schema: CODEX_REPORT_SCHEMA, model: 'sonnet', effort: 'low' }))
    .then(r => (r && !String(r.codex_status || '').startsWith('failed')) ? r : null)
}
```

`setup` は新しいブランチの作業ツリーを作る指示（`git -C <clone> worktree add <path> -b <branch> <base>`）。
`pgrep` の `[c]` は、検索するシェル自身に一致しないための書き方。

## 付録 B：続きの地点から再開する台本の骨組み

```js
// 優先度つきの共有の枠（大きさ 0 で、その種類の段階を止めて待つ）
function priorityPool(n) {
  let active = 0, seq = 0
  const queue = []
  const pump = () => {
    while (active < n && queue.length) {
      queue.sort((a, b) => a.p - b.p || a.seq - b.seq)
      const job = queue.shift(); active++
      Promise.resolve().then(job.fn).then(job.resolve, job.reject).finally(() => { active--; pump() })
    }
  }
  return (p, fn) => new Promise((resolve, reject) => { queue.push({ p, seq: seq++, fn, resolve, reject }); pump() })
}

// 記録の中の報告を参照で渡す
const ref = (file, key, base) => ({ cached: key, file, base })
const repText = rep => rep.cached
  ? `the JSON object under key "${rep.cached}" in ${rep.file} (jq '.["${rep.cached}"]' ${rep.file}); `
    + `commits after it (git log ${rep.base}..HEAD) belong to the branch too`
  : JSON.stringify(rep)

// 確認の round n から（通らなければ修正 → 確認を repair2 まで）
async function fromVerify(s, rep, reviews, n) {
  let cur = rep
  let ver = await verifyAgent(s, cur, reviews, n)
  if (!ver) return { report: cur, stopped: `verify${n}` }
  for (let round = n; round <= 2 && !passed(ver); round++) {
    const fx = await fixAgent(s, cur, { verification: ver }, `repair${round}`)
    if (!fx) return { report: cur, verify: ver, stopped: `repair${round}` }
    cur = fx
    const v2 = await verifyAgent(s, cur, reviews, round + 1)
    if (!v2) return { report: cur, verify: ver, stopped: `verify${round + 1}` }
    ver = v2
  }
  return { report: cur, verify: ver }
}
// 修正の round n から（記録の中の確認の結果を指示にする）
async function fromRepair(s, rep, reviews, n, findingsText) {
  const fx = await fixAgent(s, rep, findingsText, `repair${n}`)
  return fx ? await fromVerify(s, fx, reviews, n + 1) : { report: rep, stopped: `repair${n}` }
}

// ブランチごとの続きの地点（manifest.json にも同じものを書く）
done.k3 = fromRepair(S('k3'), ref(R, 'codex-repair1:k3', base), reviewsRef, 2, verRef(R, 'verify2:k3'))
done.r8 = fromVerify(S('r8'), ref(R, 'codex-repair1:r8', 'origin/dev'), reviewsRef, 2)
done.k6 = done.k4.then(p => ok(p) ? fresh(S('k6'), BR.k4, specNote) : { stopped: 'parent k4' })
```
