FROM python:3.11-slim

# ffmpeg/libs some audio plugins expect at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Bake model assets (e.g. Silero VAD) into the image so startup is fast/offline
RUN python agent.py download-files

# "start" = production worker mode (use "dev" for hot-reload during development)
CMD ["python", "agent.py", "start"]
