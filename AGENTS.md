# AGENTS

## Mission
- Slackワークスペース内の指定チャネルで、当日同じキーワードを含むメッセージを検知すると、決められたテンプレートで即座に返信するSlack Botを提供する。
- RTM WebSocket接続で完結する「シンプル構成」「イベントドリブン動作」「Dockerで閉じた開発体験」を採用し、単体のプロジェクトとしても迷わない運用体験を担保する。

## Guiding Principles
1. **単一責務**: コンテナはSlack RTM接続と返信処理だけに集中させる。外部DBに依存せず、必要な管理情報はインメモリまたは`data/`以下の軽量ファイルに限定する。
2. **宣言的設定**: Slack Bot Token、対象チャネル、検知キーワード、返信内容などは`.env`から読み込み、Docker Composeの環境差し替えで容易に構成変更できるようにする。
3. **観測可能性**: RTM接続状態、キーワードマッチ結果、返信の成功/失敗はINFO以上のログに出力し、`docker compose logs`だけで状況を把握できるようにする。
4. **冪等な返信**: 同日の同一メッセージに重複返信しないよう、イベント`ts`と検知キーワードをキーにメモリ上のSetへ記録して再処理を防ぐ。

## Target Stack
- **Language**: Python 3.12系（2024年時点の最新安定版）。
- **Framework/Library**: `slack_sdk`の`RTMClient`と`WebClient`。HTTPサーバーやBoltは使わない。
- **Runtime**: Docker Composeで起動する常駐サービス。RTM WebSocket接続のみなのでポートの公開は不要。
- **Storage**: 永続ボリュームは基本不要。必要なら`data/`以下にJSONキャッシュ等を置く程度。

## Architecture Overview
```
Slack RTM WebSocket -> RTMイベントハンドラ -> キーワードフィルタ -> 返信メッセージ組み立て -> Slack Web API chat.postMessage
```

### Components
1. **app**: `src/app.py`にRTM接続のブートストラップとイベントハンドラを実装。`message`イベントで対象チャネルとキーワードをチェックし返信する。
2. **logging config**: `src/logging.py`でJSON/構造化ログ設定を提供し、接続状態・メッセージID・結果を一望できるようにする。
3. **docker compose**: `docker-compose.yml`で`slackbot`サービスを定義し、`.env`を参照しつつ`python -m src.app`で起動する。ポートマッピングは不要。

### Event Flow
1. `RTMClient`がBot TokenでSlackへ接続し、再接続ロジックを開始。
2. `message`イベントを受信したら、`channel`と`.env`の`TARGET_CHANNEL`を比較。
3. メッセージ本文に`TARGET_KEYWORDS`(カンマ区切り、当日日付含む文字列にも対応)のいずれかが含まれるかチェック。
4. 該当した場合、`.env`の`REPLY_TEXT`をスレッド返信(`THREAD_REPLY=true`)または通常投稿として`WebClient.chat_postMessage`に送信。
5. 返信後は`event['ts']`を記録し、同一イベント再処理をスキップ。
6. Slashコマンド`/shukin_home`、`/shukin_office`、`/taikin`にも同様の返信ロジックを適用し、所定テンプレートを投稿する。

## Supported Commands
- `/shukin_home`: 在宅出勤の勤怠報告テンプレートを投稿。
- `/shukin_office`: 出社時の勤怠報告テンプレートを投稿。
- `/taikin`: 退勤報告テンプレートを投稿。

## Environment (.env)
```
SLACK_BOT_TOKEN=xoxb-...
TARGET_CHANNEL=C1234567890
TARGET_KEYWORDS=勤怠報告,出勤
REPLY_TEXT=定型返信テキスト
LOG_LEVEL=INFO
THREAD_REPLY=true
```
- `TARGET_KEYWORDS`はカンマ区切り。日付が固定ワードに含まれる場合は起動時に`YYYY-MM-DD`へ置換するヘルパーを検討。
- `THREAD_REPLY`を`false`にすると通常メッセージで投稿。
- RTM接続の安定化用に`RTM_PING_INTERVAL`など追加パラメータが必要になったら`.env`で受け取れるようにする。

## Docker Compose Skeleton
```yaml
version: "3.9"
services:
  slackbot:
    build:
      context: .
      dockerfile: Dockerfile
    env_file:
      - .env
    command: ["python", "-m", "src.app"]
    volumes:
      - ./src:/app
    restart: unless-stopped
```

## Development Workflow
1. `.env.example`を作成し、SlackアプリのBot Token・対象チャネルIDなどを設定。
2. `docker compose up --build`でRTMクライアントをローカル起動し、Slack管理画面でBot Tokenが有効か確認。
3. ログを監視しつつ、対象チャネルでテストキーワードを送信して自動返信を確認。
4. ビジネスロジックは`pytest`で単体テストし、キーワード判定や重複防止ロジック、RTMイベントハンドラのユニットテストをカバー。

## Open Questions / ToDo
- 再接続やネットワーク断の際にどこまで自動復旧できるか。バックオフ戦略の要否を評価。
- `TARGET_KEYWORDS`に当日日付をどう埋め込むか。環境変数テンプレート展開を導入するか検討。
- 返信メッセージの柔軟なカスタム（Jinja2等）や、特定ユーザーの除外ロジックなどが必要か継続検討。
