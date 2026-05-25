FROM python:3.11-slim

WORKDIR /app

# iconv converts the UTF-16 LE requirements.txt (Windows default) to UTF-8 for pip
COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends iconv \
    && iconv -f utf-16 -t utf-8 requirements.txt -o requirements.utf8.txt \
    && pip install --no-cache-dir -r requirements.utf8.txt \
    && rm requirements.utf8.txt \
    && apt-get purge -y iconv && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

COPY gitlab_agent/ ./gitlab_agent/

EXPOSE 8080

CMD ["adk", "web", "--port", "8080", "--host", "0.0.0.0"]
