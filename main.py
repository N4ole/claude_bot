"""Point d'entrée : lance le bot Discord."""
import logging
import sys

import config
from bot import ClaudeBot


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> None:
    setup_logging()

    if not config.TOKEN:
        logging.error(
            "DISCORD_TOKEN manquant. Copiez .env.example en .env et "
            "renseignez votre token."
        )
        sys.exit(1)

    bot = ClaudeBot()
    bot.run(config.TOKEN, log_handler=None)


if __name__ == "__main__":
    main()
