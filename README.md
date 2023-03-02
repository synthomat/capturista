# Capturista!

Capturista takes regular screen captures of websites.

It can be used to capture protected websites. Under the hood it uses the [Playwright](https://playwright.dev/python/) framework and currently supports standard web, kibana and tableau sites.  
New capture types can be easily integrated by extending the `AbstractLoader` class


### What's missing
* Configuration is very limited and the interval time is pre-defined (every 10min) right now.
* Secrets are not protected (Kibana, Tableau)
* Fail state reporting doesn't work in the UI yet.

## Installation
Create and activate virtual environment

    $ python3 -m venv venv
    $ . venv/bin/source

Install dependencies and Playwright browsers (this might take a while!)

    $ pip3 install -r requirements.txt
    $ playwright install chromium

## Run
    $ honcho start

