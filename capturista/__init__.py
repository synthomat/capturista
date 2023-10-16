import os

from flask import Flask

from capturista.web import create_app as capp


def create_app() -> Flask:
    return capp()


def main():
    app = create_app()
    app.run(
        host=os.getenv("BIND", "0.0.0.0"),
        port=os.getenv('PORT', 5000)
    )


if __name__ == '__main__':
    main()
