FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends procps && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p logs
ENV OLLAMA_URL=http://host.docker.internal:11434/api/generate
EXPOSE 8080
CMD ["python", "main.py", "--interval", "60"]
