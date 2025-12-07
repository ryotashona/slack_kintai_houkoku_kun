# ★開発途中〜★

# slack_kintai_houkoku_kun

Slack の特定チャネルで Slash コマンド(`/shukin_home`/`/shukin_office`/`/taikin`)を実行すると、
直近の「今日の報告」メッセージへ自動でテンプレート投稿します。文言や起点メッセージのキーワードを
変えたい場合は `src/app.py` の `COMMAND_TEMPLATES` と `ANCHOR_KEYWORDS` を編集してください。

## 必要なもの
- Slack アプリ (Bot Token `xoxb-***` と Socket Mode 用 App Level Token `xapp-***` が発行済み)
- Slash コマンド `/shukin_home` `/shukin_office` `/taikin` が Slack アプリに設定されていること
- Docker / Docker Compose
- Python でローカル動作させたい場合は `requirements.txt` に記載の依存関係をインストール

## セットアップ
1. `.env.example` を `.env` にコピーし、以下を設定します。
   - `SLACK_BOT_TOKEN` / `SLACK_APP_TOKEN`: Slack 管理画面から取得
   - `TARGET_CHANNEL`: Slash コマンドを受け付けるチャネル ID (`C********`)
   - `LOG_LEVEL`: 省略時は `INFO`
   - `THREAD_REPLY`: `true` で「今日の報告」投稿にスレッド返信、`false` で通常投稿
2. Slack 管理画面で Socket Mode を有効にし、Events / Commands に `app.py` が扱う Slash コマンドを登録

## 実行 (Docker)
```bash
docker compose up --build
```
起動後は Socket Mode で常時接続し、Slash コマンドを受け付けます。ログは `docker compose logs -f` で確認できます。

## ローカルテスト
アプリ本体とは別の Compose ファイルを用意しています。ソースをマウントした状態で pytest を実行できます。

```bash
docker compose -f docker-compose.test.yml run --rm tests
```

## Slash コマンドの使い方
どのチャネルでコマンドを実行しても、`TARGET_CHANNEL` に設定したチャネルへ投稿されます。
直近の「今日の報告」投稿にスレッド返信します。
- `/shukin_home`: 在宅勤務開始
- `/shukin_office`: 出社して勤務開始
- `/taikin`: 退勤報告

コマンドの文言を変更したい場合は `src/app.py` の `COMMAND_TEMPLATES` を編集します。起点となる投稿のキーワードは
同ファイルの `ANCHOR_KEYWORDS` に配列で定義されています。

## 開発メモ
- 詳細なアーキテクチャや運用ルールは `AGENTS.md` を参照してください。
- plan ツールの使い方や進捗共有ルールは `plans/README.md` にまとめています。
