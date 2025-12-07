# AGENTS

## Mission
- Slackワークスペース内の指定チャネルで、Slashコマンド入力をトリガーに当日の「今日の報告」メッセージへ即座にテンプレート投稿するSlack Botを提供する。
- Slack Bolt(Socket Mode)で完結する「シンプル構成」「イベントドリブン動作」「Dockerで閉じた開発体験」を採用し、単体のプロジェクトとしても迷わない運用体験を担保する。

## Guiding Principles
1. **単一責務**: コンテナはSlack Bolt(Socket Mode)によるイベント受信と返信処理だけに集中させる。外部DBに依存せず、必要な管理情報はインメモリまたは`data/`以下の軽量ファイルに限定する。
2. **宣言的設定**: Slack Bot Tokenや対象チャネルIDなどは`.env`から読み込み、Docker Composeの環境差し替えで容易に構成変更できるようにする。テンプレート文面・キーワードはコード内の定数で管理する。
3. **観測可能性**: Socket Mode接続状態、アンカー検索結果、返信の成功/失敗はINFO以上のログに出力し、`docker compose logs`だけで状況を把握できるようにする。
4. **シンプルな運用**: 必要な情報はコード内の定数（`COMMAND_TEMPLATES`/`ANCHOR_KEYWORDS`など）で管理し、設定箇所がバラつかないようにする。

## Target Stack
- **Language**: Python 3.13系（Slack SDK/Boltが対応している最新安定版）。
- **Framework/Library**: Slack Bolt for Python(Socket Mode)と`slack_sdk`の`WebClient`。
- **Runtime**: Docker Composeで起動する常駐サービス。Socket ModeでSlackへ常時接続するため、HTTPポートの公開は不要。
- **Storage**: 永続ボリュームは基本不要。必要なら`data/`以下にJSONキャッシュ等を置く程度。

## Architecture Overview
```
Slack Socket Mode -> Boltアプリ -> キーワードフィルタ -> 返信メッセージ組み立て -> Slack Web API chat.postMessage
```

### Components
1. **app**: `src/app.py`にBoltアプリのブートストラップを実装。Socket Modeでslashコマンドイベントを購読し、対象チャネルの「今日の報告」を探して返信する。
2. **logging config**: `src/logging.py`でJSON/構造化ログ設定を提供し、接続状態・メッセージID・結果を一望できるようにする。
3. **docker compose**: `docker-compose.yml`で`slackbot`サービスを定義し、`.env`を参照しつつ`python -m src.app`で起動する。HTTP待受は不要だが、BoltのSocketモード用の環境変数を渡す。

### Event Flow
1. BoltアプリがSocket Mode(App Level Token)でSlackへ接続し、再接続ロジックを開始。
2. Slashコマンド`/shukin_home`、`/shukin_office`、`/taikin`のいずれかを受信したら、呼び出し元チャネルに関係なく`.env`の`TARGET_CHANNEL`を参照して投稿先を決定する。
3. `TARGET_CHANNEL`で指定したチャネルの投稿を最新から遡り、本文に固定キーワード（例: 「今日の報告はここに」）が含まれている起点メッセージを探す。途中に他ユーザーの通常投稿が挟まっていても、キーワード一致した直近メッセージを優先。
4. 対象メッセージが見つかったら、コード内`COMMAND_TEMPLATES`で管理するテンプレートを、そのメッセージへのスレッド返信(`THREAD_REPLY=true`)として`WebClient.chat.postMessage`に送信。スレッド投稿できない場合のみ通常投稿にフォールバック。

## Supported Commands
- `/shukin_home`: 在宅出勤の勤怠報告テンプレートを投稿。
- `/shukin_office`: 出社時の勤怠報告テンプレートを投稿。
- `/taikin`: 退勤報告テンプレートを投稿。

## Environment (.env)
```
# スラック側で作成したBotトークン
SLACK_BOT_TOKEN=xoxb-...
# Socket Mode用のApp-Level Token
SLACK_APP_TOKEN=xapp-...
# 監視・返信対象のチャネルID
TARGET_CHANNEL=C1234567890
# 出力ログレベル
LOG_LEVEL=INFO
# trueならスレッド返信、falseなら通常投稿
THREAD_REPLY=true
```
- `THREAD_REPLY`を`false`にすると通常メッセージで投稿。
- Socket Modeの再接続間隔などを調整したい場合は、Boltの設定値を`.env`経由で受け取れるようにする。

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
2. `docker compose up --build`でBolt(Socket Mode)アプリをローカル起動し、Slack管理画面でBot Token/App Tokenが有効か確認。
3. ログを監視しつつ、対象チャネルでテストキーワードを送信して自動返信を確認。
4. ビジネスロジックは`pytest`で単体テストし、キーワード判定やヘルパーロジックをカバー。
5. コミットメッセージは日本語で記述し、変更内容が一目で分かる形にする。
6. エージェント作業時は「plan作成 → 作業 → 作業履歴共有 → plan更新」の順で進捗を共有し、詳細は`plans/README.md`を参照する。コンテキストウィンドウをクリアする場合でも、同ファイルに沿ってPlanを維持すれば作業を継続できる。

## Open Questions / ToDo
- 再接続やネットワーク断の際にどこまで自動復旧できるか。バックオフ戦略の要否を評価。
- 返信メッセージの柔軟なカスタム（Jinja2等）や、特定ユーザーの除外ロジックなどが必要か継続検討。
