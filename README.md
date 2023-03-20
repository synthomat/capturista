# Capturista!

Capturista takes regular screen captures of websites.

It can be used to capture protected websites. Under the hood it uses the [Playwright](https://playwright.dev/python/) framework and currently supports standard web, kibana and tableau sites.  
New capture types can be easily integrated by extending the `AbstractLoader` class

### Requirements
* Python 3

### Stack
* **Python 3** and **Flask**
* **Playwright** for screenshots
* **Pillow** for post-processing images
* **AlpineJS** and **HTMX** for UI

### What's missing
* Configuration is very limited and the interval time is pre-defined (every 10min) right now.
* Secrets are not protected (Kibana, Tableau)
* Fail state reporting doesn't work in the UI yet.
* Only sequential captures
* TinyDB sometimes corrupts the database (writes database twice) ¯\\\_(ツ)\_/¯

## Installation
Create and activate virtual environment

    $ python3 -m venv venv
    $ . venv/bin/activate

Install dependencies and Playwright browsers (this might take a while!)

    $ pip3 install -r requirements.txt
    $ playwright install chromium

## Run
    $ honcho start

## Docker

**Build image**

    $ docker build -t capturista .

**Run image**

    $ touch db.json
    $ docker run -p 8000:8000 -v ${PWD}/db.json:/app/db.json capturista:latest

The tool is accessible at http://localhost:8000

**Or Docker Compose**

    $ touch db.json
    $ docker volume create caddy_data
    $ docker-compose up -d

The tool is accessible at http://localhost