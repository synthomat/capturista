FROM python:3.11-slim-bullseye

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# Following dependencies will run inside the container
# RUN playwright install chromium
# RUN playwright install-deps

COPY . .

EXPOSE 8000
CMD ["./entrypoint.sh"]