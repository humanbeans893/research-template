# NNN_<slug>: <実験タイトル>

- **日付**: YYYY-MM-DD
- **今の結論と状態**: [summary.md](summary.md)。この README は経緯の記録です。古い記述は消さず、訂正は末尾の「訂正・追記」に日付をつけて足します。

## 目的

<この実験で何を確かめたいか。判定の規則は summary.md に書く。>

## 背景

<なぜこの実験が必要か。先行する実験(例: `003_baseline_fit`)や決定(`docs/decision-NNN-...`)への参照。>

## 方法

- パラメータ: `params.py`(値の正。ここには要点だけ)
- 入力: <使うデータと上流の表。他の実験の `out/` は読まない。>
- 実行(smoke で通して各段の所要時間を見てから本実行):

```bash
docker compose exec research-template uv run python experiments/NNN_<slug>/run.py --smoke
docker compose exec research-template uv run python experiments/NNN_<slug>/run.py
```

## 結果

<本実行の日付とコミット(`out/params_used.json`)、得られた図・数値。数値には出所の CSV(行・列)を添え、図表は `out/` のファイル名で参照する。>

## 考察

<結果から何が言えるか。想定との差分。>

## 次にやること

- [ ] <次の実験・確認事項>

## 訂正・追記

<日付をつけて足す。前の記述は消さない。なければ「なし」。>
