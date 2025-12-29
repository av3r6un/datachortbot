FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
  libopus0 \
  ffmpeg \
  build-essential && rm -rf /var/lib/apt/lists/*

RUN useradd -m botuser
WORKDIR /app
COPY ./req.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app/bot

RUN mkdir -p /web/storage && chown -R botuser:botuser /web/storage
RUN mkdir -p /app/bot/logs && chown -R botuser:botuser /app/bot/logs

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER root
ENTRYPOINT [ "/entrypoint.sh" ]

USER botuser
CMD ["python", "-m", "bot"]
