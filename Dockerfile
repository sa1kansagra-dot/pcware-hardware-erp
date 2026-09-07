FROM python:3.11-slim

WORKDIR /app

# Copy application files
COPY . /app

# Ensure SQLite DB has correct permissions
RUN chmod -R 755 /app

# Default cloud port
ENV PORT=8080
EXPOSE 8080

CMD ["python3", "server.py"]
