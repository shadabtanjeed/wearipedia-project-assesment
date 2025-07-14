# Fitbit Data Ingestion Pipeline

## Overview

This project implements a daily, delta-load pipeline for ingesting Fitbit health metrics into a local TimescaleDB instance. It supports batch and incremental loads, automates ingestion via cron, and uses Docker for portability and reproducibility.

---

## Directory Structure

```
wearipedia-project-assesment/
├── .gitattributes
├── .gitignore
├── Challenge v2.pdf
├── README.md
├── repomix-output.xml
├── requirements.txt
├── .vscode/
│   └── settings.json
├── Data/
│   ├── Modified Data/      # synthetic data for 2 users 
│   └── Raw Data/           # Raw synthetic data files
├── Task 0a/                # Data volume analysis
├── Task 0b/                # Synthetic data generation
└── Task 1/                 # Data ingestion pipeline
    ├── crontab
    ├── db_operations.py
    ├── device_manager.py
    ├── docker-compose.yml
    ├── Dockerfile
    ├── entrypoint.sh
    ├── example_json.txt
    ├── fix_source_adapter.py
    ├── ingestions.py
    ├── json_structure.txt
    ├── models.py
    ├── schema.sql
    └── source_adapter.py
```

---

## Key Features

- **Delta-Load Processing:** Tracks last processed timestamps for each metric/user.
- **Factory & Adapter Patterns:** Modular handling of metrics and data sources.
- **Persistence:** Data stored in both files and TimescaleDB for redundancy.
- **Time-Series Optimization:** Uses TimescaleDB hypertables for efficient queries.
- **Containerization:** Dockerized for consistent environments.
- **Automated Scheduling:** Cron jobs for daily ingestion.
- **Multiple Modes:** Normal, test, catch-up, and reset.

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Synthetic data files from Task 0b in `Data/Modified Data`

### Setup

1. Clone the repository:
   ```sh
   git clone [repository-url]
   cd wearipedia-project-assesment
   ```
2. Ensure data files are in `Data/Modified Data`.

    The following files are not tracked by git:

    - Data/Raw Data/complete_user1_raw.json
    - Data/Raw Data/hr_user1_raw.json
    - Data/Raw Data/complete_user2_raw.json
    - Data/Raw Data/hr_user2_raw.json

    ## Downloading the Data Files

    You can obtain the required data files using the following instructions, depending on your operating system.

    ### Windows

    ```powershell
    # Create the directory if it doesn't exist
    New-Item -Path "Data/Raw Data" -ItemType Directory -Force

    # Download the files
    Invoke-WebRequest -Uri "https://drive.google.com/uc?export=download&id=17JDEIkw29NgXiyFmowiQv9E68_pKWwGc" -OutFile "Data/Raw Data/complete_user1_raw.json"
    Invoke-WebRequest -Uri "https://drive.google.com/uc?export=download&id=1uDgV2LYx8UNOCq-JtgbFg-PYQgUaLde2" -OutFile "Data/Raw Data/hr_user1_raw.json"
    Invoke-WebRequest -Uri "https://drive.google.com/uc?export=download&id=13VVG80CODeIiH02Mw2ihuFmQWLvHeJ2h" -OutFile "Data/Raw Data/complete_user2_raw.json"
    Invoke-WebRequest -Uri "https://drive.google.com/uc?export=download&id=1eFTYoqBpcV1T_4cie8qTZ-LgIsjPpLjd" -OutFile "Data/Raw Data/hr_user2_raw.json"

    Write-Host "All data files downloaded successfully!" -ForegroundColor Green
    ```

    ### Linux / macOS

    ```bash
    # Create the directory if it doesn't exist
    mkdir -p "Data/Raw Data"

    # Download the files
    curl -L "https://drive.google.com/uc?export=download&id=17JDEIkw29NgXiyFmowiQv9E68_pKWwGc" -o "Data/Raw Data/complete_user1_raw.json"
    curl -L "https://drive.google.com/uc?export=download&id=1uDgV2LYx8UNOCq-JtgbFg-PYQgUaLde2" -o "Data/Raw Data/hr_user1_raw.json"
    curl -L "https://drive.google.com/uc?export=download&id=13VVG80CODeIiH02Mw2ihuFmQWLvHeJ2h" -o "Data/Raw Data/complete_user2_raw.json"
    curl -L "https://drive.google.com/uc?export=download&id=1eFTYoqBpcV1T_4cie8qTZ-LgIsjPpLjd" -o "Data/Raw Data/hr_user2_raw.json"

    echo "All data files downloaded successfully!"
    ```

    ### Using wget

    ```bash
    # Create the directory if it doesn't exist
    mkdir -p "Data/Raw Data"

    # Download the files
    wget -O "Data/Raw Data/complete_user1_raw.json" "https://drive.google.com/uc?export=download&id=17JDEIkw29NgXiyFmowiQv9E68_pKWwGc"
    wget -O "Data/Raw Data/hr_user1_raw.json" "https://drive.google.com/uc?export=download&id=1uDgV2LYx8UNOCq-JtgbFg-PYQgUaLde2"
    wget -O "Data/Raw Data/complete_user2_raw.json" "https://drive.google.com/uc?export=download&id=13VVG80CODeIiH02Mw2ihuFmQWLvHeJ2h"
    wget -O "Data/Raw Data/hr_user2_raw.json" "https://drive.google.com/uc?export=download&id=1eFTYoqBpcV1T_4cie8qTZ-LgIsjPpLjd"

    echo "All data files downloaded successfully!"
    ```
    You can also download the files manually from the links provided in the `Data/Raw Data` directory: https://drive.google.com/drive/folders/1883VBRmFepECPhCCWwYBObX7BW7li8VK?usp=drive_link

3. Build and run containers:
   ```sh
   cd Task\ 1
   docker-compose up -d
   ```

### Operation Modes

- **Normal (daily cron, run once each day to retrieve data of one day only starting from 01-01-2024 or last run timestamp):**
  ```sh
  docker-compose up -d
  ```
- **Test (2-min intervals; run with 2 mins interval, each time retrive data just like in Normal mode.):**
  ```sh
  TEST_MODE=true docker-compose up -d
  ```
- **Catch-up (retrieve all data at once up to 2024-01-30):**
  ```sh
  CATCH_UP_MODE=true docker-compose up -d
  ```
- **Reset (clear all data stored into db and run Normal mode):**
  ```sh
  RESET_MODE=true docker-compose up -d
  ```

---

## Usage

### Ingestion Script Arguments

- Process specific user:
  ```sh
  docker-compose exec ingestion python ingestions.py --user-id 1
  ```
- Process specific metric:
  ```sh
  docker-compose exec ingestion python ingestions.py --metric-type heart_rate
  ```
- Debug logging:
  ```sh
  docker-compose exec ingestion python ingestions.py --debug
  ```
- Reset timestamps:
  ```sh
  docker-compose exec ingestion python ingestions.py --reset-timestamps
  ```
- Single day processing:
  ```sh
  docker-compose exec ingestion python ingestions.py --single-day
  ```
- Check file mappings:
  ```sh
  docker-compose exec ingestion python ingestions.py --check-files
  ```

### Timestamp Tracking

- Timestamp files: `last_timestamp_<metric_type>_user_<user_id>.txt`
- Remove all:
  ```sh
  rm last_timestamp_*.txt
  ```

### TimescaleDB Only

- Run DB container:
  ```sh
  docker-compose up -d timescaledb
  ```
- Connect:
  ```sh
  docker-compose exec timescaledb psql -U postgres -d fitbit_data
  ```

---

## Technical Details

### Database Schema

- **Users Table:** Stores user info
- **Devices Table:** Device info, user association
- **Metric Tables:** Separate for each metric (heart rate, SPO2, HRV, etc.)
- **Last Processed Dates:** Tracks per metric/user

Example:
```sql
CREATE TABLE IF NOT EXISTS USERS (
    USER_ID INT PRIMARY KEY,
    USERNAME VARCHAR(255),
    EMAIL VARCHAR(255),
    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS DEVICES (
    DEVICE_ID VARCHAR(255) PRIMARY KEY,
    USER_ID INT REFERENCES USERS(USER_ID),
    DEVICE_TYPE VARCHAR(50),
    MODEL VARCHAR(100),
    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS HEART_RATE (
    ID SERIAL PRIMARY KEY,
    USER_ID INT REFERENCES USERS(USER_ID),
    DEVICE_ID VARCHAR(255) REFERENCES DEVICES(DEVICE_ID),
    TIMESTAMP TIMESTAMP NOT NULL,
    VALUE INT,
    RESTING_HEART_RATE INT,
    ZONES JSONB,
    SUMMARY JSONB,
    INTRADAY JSONB
);
```
- Uses JSONB for nested/complex metric data.

---

## Pipeline Architecture

1. **Initialization:** DB connection, schema check
2. **Data Source:** Adapter connects to synthetic data
3. **Delta Detection:** Timestamp check for new data
4. **Extraction:** Fetch new data
5. **Transformation:** Factory converts raw to metric objects
6. **Loading:** Insert into DB tables
7. **State Tracking:** Update timestamps
8. **Scheduling:** Cron schedules next run

### Key Components

- **Source Adapter:** Abstracts data source (synthetic, future API)
- **Metric Models:** Factory for metric objects
- **DB Operations:** Handles all DB logic
- **Entrypoint Script:** Manages container mode, cron setup

---

## Design Choices

- **Python:** Chosen for data processing, PostgreSQL integration, readability, and ecosystem.
- **TimescaleDB:** SQL interface, relational features, ACID compliance, PostgreSQL compatibility.
- **JSONB Storage:** Flexible, future-proof, efficient for nested health metrics.
- **Synthetic Data:** No API dependency, reproducible, controlled testing, easy future API integration.

---

## Extensibility

Adding support for a new type of watch (e.g., Garmin, Apple Watch) involves extending the adapter and factory patterns:

### 1. Create a New Source Adapter

Implement a new adapter class that knows how to read and parse data from the new watch's format:

```python
# source_adapter.py

class GarminAdapter(SourceAdapter):
    def fetch_data(self, user_id, metric_type, since_timestamp):
        # Custom logic to read Garmin data files or API
        raw_data = self._read_garmin_files(user_id, metric_type, since_timestamp)
        return raw_data

    def _read_garmin_files(self, user_id, metric_type, since_timestamp):
        # Example: parse Garmin CSV/JSON files
        # Return standardized dict/list
        pass
```

Register the adapter in the factory:

```python
# fix_source_adapter.py

def get_adapter(source_type):
    if source_type == "fitbit":
        return FitbitAdapter()
    elif source_type == "garmin":
        return GarminAdapter()
    # Add more adapters as needed
```

### 2. Extend Metric Models

If the new watch provides unique metrics, add corresponding model classes:

```python
# models.py

class GarminHeartRate(MetricBase):
    def __init__(self, user_id, device_id, timestamp, value, stress_level):
        super().__init__(user_id, device_id, timestamp)
        self.value = value
        self.stress_level = stress_level
```

### 3. Update Configuration

Specify the new source type via CLI or environment variable:

```sh
SOURCE_TYPE=garmin docker-compose up -d
```

### 4. Add Database Schema

Extend `schema.sql` for new metrics or device types:

```sql
CREATE TABLE IF NOT EXISTS GARMIN_HEART_RATE (
    ID SERIAL PRIMARY KEY,
    USER_ID INT REFERENCES USERS(USER_ID),
    DEVICE_ID VARCHAR(255) REFERENCES DEVICES(DEVICE_ID),
    TIMESTAMP TIMESTAMP NOT NULL,
    VALUE INT,
    STRESS_LEVEL INT
);
```

### Summary

- Implement a new adapter for the watch data format.
- Extend metric models for new metrics.
- Register the adapter in the factory.
- Update configuration and schema as needed.

This modular approach allows seamless integration of new devices with minimal changes to the core pipeline.

---

## Support

For issues or questions, open a GitHub issue or contact the development team.

