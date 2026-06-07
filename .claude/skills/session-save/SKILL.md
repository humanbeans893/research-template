# /session-save

セッションの作業内容をClaude メモリとユーザー向けMarkdownの2箇所に保存する。

## When to use

- セッション終了時に作業内容を記録したいとき
- 長時間のセッション後に進捗を保存したいとき
- ユーザーが「セッションを保存して」「作業内容をまとめて」と言ったとき

## Steps

### 1. 情報収集

会話を振り返り、以下を整理する：

```bash
git status
git diff --name-only HEAD
git log --oneline -5
```

整理する項目：
- 今回のセッションで行った作業（要約）
- 変更したファイルと変更内容
- 下した判断・決定事項
- 未解決の課題
- 次のステップ

### 2. ユーザー確認

整理した内容をユーザーに提示し、確認を求める。修正があれば反映する。

**重要**: 確認なしにメモリへ書き込まないこと。誤った情報がメモリに入ると以降のセッションに悪影響を与える。

### 3. メモリ更新

メモリディレクトリ: プロジェクトの auto memory ディレクトリ（MEMORY.md があるディレクトリ）

#### 既存メモリの更新
- MEMORY.md を読み、関連する既存メモリファイルがあれば**内容を上書き更新**する（追記ではなく現在の状態に更新）
- メモリには次回以降のセッションで有用な情報のみを書く（一時的な作業状態は書かない）

#### 新規メモリの作成（必要な場合のみ）
新しいトピックが出た場合、YAML frontmatter 形式で作成：

```markdown
---
name: <トピック名>
description: <1行の説明>
type: <user|feedback|project|reference>
---

<内容>

**Why:** <理由>

**How to apply:** <次回セッションでの活用方法>
```

#### MEMORY.md インデックス更新
新規ファイルを作成した場合、MEMORY.md にエントリを追加：
```
- [タイトル](filename.md) — 1行の説明
```

### 4. セッションログ作成

ディレクトリ `.claude/sessions/` に以下の命名規則でファイルを作成：

```
.claude/sessions/YYYY-MM-DD_HH-MM_<slug>.md
```

- `<slug>`: 作業内容を表す短い英語（例: `paper-revision`, `eddy-analysis`）
- 時刻はセッション保存時点の現在時刻を使用

テンプレート：

```markdown
# Session: <タイトル>

- **Date**: YYYY-MM-DD HH:MM
- **Branch**: <ブランチ名>

## Summary

- <箇条書きで作業内容>

## Files Modified

| File | Change |
|------|--------|
| path/to/file | 変更内容の簡潔な説明 |

## Decisions Made

- <判断・決定事項>

## Open Issues

- <未解決の課題（なければ「None」）>

## Next Steps

- [ ] <次にやること>
```

### 5. 完了報告

保存先を表示する：
- メモリファイルのパス（更新/作成したもの）
- セッションログのパス
