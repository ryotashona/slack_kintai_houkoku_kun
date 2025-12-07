import os

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from .logging_config import configure_logging


def create_app() -> App:
    configure_logging()
    app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

    # TODO: register message listeners and slash commands

    return app


def main() -> None:
    app_token = os.environ.get("SLACK_APP_TOKEN")
    if not app_token:
        raise RuntimeError("SLACK_APP_TOKEN is not set")

    app = create_app()
    handler = SocketModeHandler(app, app_token)
    handler.start()


if __name__ == "__main__":
    main()
