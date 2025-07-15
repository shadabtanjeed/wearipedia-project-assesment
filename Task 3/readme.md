# Task 3: Optimizing Design for Multi-Year / Multi-User queries

This task is about making database queries for heart rate data faster and more efficient, especially when dealing with large amounts of data over long periods or for many users. The main idea is to use smart aggregation techniques so that queries run quickly and use fewer resources.

For this project, I focused on heart rate data, but the same approach can be used for other metrics like breathing rate (br) or heart rate variability (hrv).

**Note:** 
- There’s no Dockerfile included because the code is meant to run directly on a PostgreSQL database. You’ll find SQL scripts and Python code that should be executed in a PostgreSQL environment.

- This task is based on the same TimeScaleDB database used in Task 2 and Task 1, sit is recommended to do the same.

## How Data Aggregation Works

There are two main files:
- `heart_rate_aggregations.sql`: Contains SQL functions and procedures to create and manage heart rate data aggregations.
- `run_aggregations.py`: A Python script that runs these aggregations based on the time intervals you need.

### What the SQL File Does

- **Creates Aggregation Views:** The SQL file sets up views that summarize heart rate data at different time levels: 1 minute, 1 hour, 1 day, 1 week, and 1 month.
    - For example, `heart_rate_1m` summarizes raw data into 1-minute buckets, grouped by user and device, and calculates stats like average, min, max, and count.
    - Higher-level views (`1h`, `1d`, `1w`, `1mo`) further aggregate the data into hourly, daily, weekly, and monthly summaries.

- **Refresh Policies:** The system automatically keeps the 1-minute view (`heart_rate_1m`) up to date using TimescaleDB’s continuous aggregates. Other views can be refreshed manually as needed.

- **Helper Functions:**
    - `refresh_heart_rate_aggregation(level, start_date, end_date)`: Returns the right SQL command to refresh a specific aggregation level.
    - `get_optimal_heart_rate_table(start_date, end_date)`: Suggests the best table or view to use for a given date range, so queries are always as efficient as possible.
        - For short ranges, use raw data.
        - Up to 7 days: use hourly data.
        - Up to 30 days: use daily data.
        - Up to 90 days: use weekly data.
        - Over 90 days: use monthly data.
    - `get_heart_rate_aggregation_stats()`: Provides stats about each aggregation view, like last refresh time, table size, and row count. This helps with monitoring and debugging.

### What the Python Script Does
It first connects to the PostgreSQL database, using the credentials provided in the `get_db_connection()` function. 

Then it creates the aggregations by calling the `setup_aggregations(conn)` function, which executes the SQL commands to create the necessary views.

After that, it can refresh specific aggregations using the `refresh_aggregation(conn, level, start_date, end_date)` function. This function takes a level (like `1h` for hourly) and a date range to refresh the data for that level.

Finally, it can execute the refresh commands using the `execute_refresh(conn, level, start_date, end_date)` function, which runs the SQL commands returned by `refresh_heart_rate_aggregation()`.

It can also get stats about the aggregations using the `get_stats(conn)` function, which retrieves information like the last refresh time and row count for each aggregation view.

## How to Run the Aggregation System

Follow these steps to set up and use the heart rate data aggregation system:

### 1. Start the TimescaleDB Database

Make sure the TimescaleDB instance from previous tasks is running:

```bash
cd "Task 1"
docker compose up -d timescaledb
```

### 2. Apply the SQL Aggregation Script

Connect to the database and execute the SQL file to set up aggregation views and functions:

```bash
cd "Task 1"
docker compose exec -T timescaledb psql -U postgres -d fitbit_data < "../Task 3/db_optimizations/heart_rate_aggregations/heart_rate_aggregations.sql"
```

### 3. Run the Python Aggregation Script

Set up your environment and run the Python script to initialize aggregations:

```bash
cd "Task 3/db_optimizations/heart_rate_aggregations"
python run_aggregations.py --setup
```

### 4. Refresh Aggregations

Refresh the aggregation levels in order, starting from 1-minute up to monthly:

```bash
python run_aggregations.py refresh 1m --execute
python run_aggregations.py refresh 1h --execute
python run_aggregations.py refresh 1d --execute
```

To refresh a specific aggregation level for a custom date range:

```bash
python run_aggregations.py refresh 1mo --start 2024-01-01 --end 2024-01-22 --execute
```

### 5. View Aggregation Stats

Get statistics about the current state of the aggregations:

```bash
python run_aggregations.py stats
```

### 6. Test Automatic Query Optimization

You can verify which aggregation table is optimal for a given date range by running the following SQL queries in your PostgreSQL client (e.g., DBeaver):

```sql
SELECT get_optimal_heart_rate_table('2024-01-01', '2024-01-01 01:00:00');  -- Returns 'heart_rate'
SELECT get_optimal_heart_rate_table('2024-01-01', '2024-01-05');           -- Returns 'heart_rate_1h'
SELECT get_optimal_heart_rate_table('2024-01-01', '2024-01-20');           -- Returns 'heart_rate_1d'
SELECT get_optimal_heart_rate_table('2024-01-01', '2024-03-01');           -- Returns 'heart_rate_1w'
SELECT get_optimal_heart_rate_table('2024-01-01', '2025-01-01');           -- Returns 'heart_rate_1mo'
```

You can use any SQL client to run these queries.
