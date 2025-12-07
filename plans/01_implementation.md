# Implementation Plan

## 1. 足場作成 (Scaffolding)
- [x] `.env.example`を追加し、`AGENTS.md`に記載した環境変数を定義。
- [x] Python依存関係用に`pyproject.toml`または`requirements.txt`を用意し、`slack_bolt`/`slack_sdk`など必要ライブラリを記述。
- [x] `Dockerfile`と`docker-compose.yml`を作成し、Python 3.13系イメージで`python -m src.app`が動くよう設定。
- [x] `src/`配下に`app.py`、`logging_config.py`などの雛形を用意。

## 2. Bolt(Socket Mode)ボット実装
- [ ] `src/app.py`でBoltアプリと`WebClient`の初期化、Socket Mode接続、再接続ロジックを実装。
- [ ] 対象チャネルで最新の`TARGET_KEYWORDS`一致メッセージを検索するヘルパーを実装。
- [ ] `/shukin_home`、`/shukin_office`、`/taikin`のSlashコマンドハンドラを追加し、テンプレート投稿処理をまとめる。
- [ ] ログ出力を`logging_config`で設定（JSON/構造化ログ想定）。

## 3. ドキュメント・テスト・検証
- [ ] `README.md`にセットアップ方法、コマンド一覧、plan運用などを追記。
- [ ] `pytest`ベースの単体テストを`tests/`に追加し、キーワード検索・冪等確認などを検証。
- [ ] 開発フローに沿って`docker compose up`で動作確認し、ログ/コマンド動作を確認。
