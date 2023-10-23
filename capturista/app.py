import logging
import os

from flask import Flask

from capturista.web import create_app as capp


def create_app() -> Flask:
    return capp()


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def main():
    app = create_app()
    server_config = dict(
        host=os.getenv("BIND", "0.0.0.0"),
        port=os.getenv('PORT', 5000)
    )

    logger.info("Listening on %s", server_config)

    app.run(**server_config)


if __name__ == '__main__':
    main()
