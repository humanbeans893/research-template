# NNN_<slug>: <実験タイトル>

- **日付**: YYYY-MM-DD
- **ステータス**: 進行中 | 完了 | 中止

## 目的

<この実験で何を確かめたいか。>

## 背景

<なぜこの実験が必要か。先行する実験(`experiments/NNN_...`)や決定(`docs/decision-NNN-...`)への参照。>

## 方法

- パラメータ: `params.py` を参照(重要なものはここに要約する)
- 実行コマンド:

```bash
docker compose exec research-template uv run python experiments/NNN_<slug>/run.py
```

## 結果

<得られた図・数値。`out/` 内のファイル名で参照する。>

## 考察

<結果から何が言えるか。想定との差分。>

## 次にやること

- [ ] <次の実験・確認事項>
