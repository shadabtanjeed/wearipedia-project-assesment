FROM python:3.9-slim

WORKDIR /app

# Install cron and required packages
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py /app/
COPY *.sql /app/
COPY entrypoint.sh /app/
COPY crontab /etc/cron.d/ingestion-cron

# Make crontab file executable
RUN chmod 0644 /etc/cron.d/ingestion-cron
RUN crontab /etc/cron.d/ingestion-cron

# Create directory for logs
RUN mkdir -p /var/log/ingestion

# Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Run entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]