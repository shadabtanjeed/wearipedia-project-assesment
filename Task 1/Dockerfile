FROM python:3.9-slim

# Install cron and other dependencies
RUN apt-get update && apt-get install -y \
    cron \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /var/log

# Copy cron job and set permissions
COPY crontab /etc/cron.d/ingestion-cron
RUN chmod 0644 /etc/cron.d/ingestion-cron
RUN crontab /etc/cron.d/ingestion-cron

# Create state directory for timestamp storage
RUN mkdir -p /app/state

# Create entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Start with entrypoint
ENTRYPOINT ["/entrypoint.sh"]