FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY setup.py .
COPY bot/ ./bot/
COPY . .

RUN pip install -e .

ENV BOT_TOKEN=""

ENV RAILWAY_DISABLE_HEALTHCHECK=true

CMD ["python", "-m", "bot.main"]
