"""Entry point for the Twitter Bot GUI.

Author: Adrián Martínez Fuentes
Project: Twitter Bot
"""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from twitter_bot.controller import TwitterBotController

LOG_DIR = Path(__file__).parent / "logs"


def configure_logging():
    LOG_DIR.mkdir(exist_ok=True)
    handler = RotatingFileHandler(LOG_DIR / "twitter_bot.log", maxBytes=1_000_000, backupCount=3)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler])


def main():
    configure_logging()
    controller = TwitterBotController()
    controller.view.root.mainloop()


if __name__ == "__main__":
    main()
