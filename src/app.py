import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from .logging_config import configure_logging

# Slashコマンドごとに投稿するテンプレートを1:1で定義。
# 仕組み自体は共通なので、ここに文言を追記/変更するだけでよい。
COMMAND_TEMPLATES: Dict[str, str] = {
    "/shukin_home": "{user} 在宅で業務開始します。",
    "/shukin_office": "{user} 出社して業務開始します。",
    "/taikin": "{user} 本日の業務を終了します。",
}

ANCHOR_KEYWORDS = [
    # Slack上で毎朝流れる「今日の報告」投稿。複数あればここへ追記する。
    "今日の勤怠報告はこちら",
]


@dataclass
class BotSettings:
    target_channel: str
    keywords: List[str]
    thread_reply: bool


def load_settings() -> BotSettings:
    """Read environment variables and normalize settings."""
    target_channel = os.getenv("TARGET_CHANNEL")
    if not target_channel:
        raise RuntimeError("TARGET_CHANNEL is not set")

    thread_reply = _to_bool(os.getenv("THREAD_REPLY", "true"))

    return BotSettings(
        target_channel=target_channel,
        keywords=_expand_keywords(",".join(ANCHOR_KEYWORDS)),
        thread_reply=thread_reply,
    )


def register_handlers(app: App, settings: BotSettings) -> None:
    def command_handler(command_name: str):
        # Slashコマンドごとにテンプレートだけ変わり、処理は共通。
        # ボイラープレートを抑えるためクロージャで生成。
        template = COMMAND_TEMPLATES.get(command_name, "")

        def _handler(ack, body, respond, client: WebClient, logger):
            ack()
            user_id = body.get("user_id")

            anchor = _find_anchor_message(client, settings.target_channel, settings.keywords, logger)
            if not anchor:
                respond("「今日の報告」メッセージが見つかりませんでした。")
                return

            anchor_ts = anchor.get("ts")
            text = _build_reply_text(template, user_id)
            success = _post_reply(
                client,
                channel=settings.target_channel,
                thread_ts=anchor_ts if settings.thread_reply else None,
                text=text,
            )
            if success:
                respond(f"<#{settings.target_channel}> に報告を投稿しました。")
            else:
                respond("投稿に失敗しました。ログを確認してください。")

        return _handler

    for command_name in COMMAND_TEMPLATES:
        app.command(command_name)(command_handler(command_name))


def _find_anchor_message(
    client: WebClient,
    channel_id: str,
    keywords: List[str],
    logger: logging.Logger,
    history_limit: int = 200,
) -> Optional[dict]:
    try:
        response = client.conversations_history(channel=channel_id, limit=history_limit)
    except SlackApiError as exc:
        logger.error("Failed to fetch channel history: %s", exc)
        return None

    for message in response.get("messages", []):
        text = message.get("text", "")
        if _match_keyword(text, keywords):
            return message
    return None


def _match_keyword(text: str, keywords: List[str]) -> Optional[str]:
    for keyword in keywords:
        if keyword and keyword in text:
            return keyword
    return None


def _post_reply(client: WebClient, channel: str, text: str, thread_ts: Optional[str]) -> bool:
    try:
        payload = {"channel": channel, "text": text, "link_names": True}
        if thread_ts:
            payload["thread_ts"] = thread_ts
        client.chat_postMessage(**payload)
        return True
    except SlackApiError as exc:
        logging.getLogger(__name__).error("Failed to post reply: %s", exc)
        return False


def _build_reply_text(template: str, user_id: Optional[str]) -> str:
    """Return the final text by injecting <@user> mention when possible."""
    if not user_id:
        return template

    mention = f"<@{user_id}>"
    if "{user}" in template:
        return template.replace("{user}", mention)
    return f"{mention} {template}".strip()


def _expand_keywords(raw_value: str) -> List[str]:
    today = datetime.now().strftime("%Y-%m-%d")
    keywords = []
    for keyword in (item.strip() for item in raw_value.split(",") if item.strip()):
        keyword = keyword.replace("{YYYY-MM-DD}", today).replace("{DATE}", today)
        keywords.append(keyword)
    return keywords


def _to_bool(value: str) -> bool:
    return value.lower() in {"1", "true", "yes", "on"}


def create_app() -> App:
    load_dotenv()
    configure_logging()

    bot_token = os.getenv("SLACK_BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("SLACK_BOT_TOKEN is not set")

    app = App(token=bot_token)
    settings = load_settings()
    register_handlers(app, settings)
    return app


def main() -> None:
    app_token = os.getenv("SLACK_APP_TOKEN")
    if not app_token:
        raise RuntimeError("SLACK_APP_TOKEN is not set")

    app = create_app()
    handler = SocketModeHandler(app, app_token)
    handler.start()


if __name__ == "__main__":
    main()
