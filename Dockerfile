FROM python:3.11-slim-bullseye

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
RUN playwright install chromium

COPY . .

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0", "capturista:create_app()"]