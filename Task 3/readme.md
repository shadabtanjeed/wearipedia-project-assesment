- the active zone minute varies by 1 min. So, the aggregartion can be hourly, daily, weekly, monthly

- activity is a daily record. So, you can aggregate it weekly, monthly

- Similarly breathing rate is a daily record. So, you can aggregate it weekly, monthly

- heart rate differs by 1 sec. So you can aggregate it per minute, hourly, daily, weekly, monthly

- hear rate zone has daily values. So, you can aggregate it weekly, monthly. but remember that the heart rate zone + hear rate was originally a composite relation which broken down into two, so choose the monthly and weekly aggregates in such way that they match

- hrv differs per minute. So, the aggregartion can be hourly, daily, weekly, monthly

- spo2  differs per minute. So, the aggregartion can be hourly, daily, weekly, monthly.

Also be mindful of the fact that there could be already existing aggregate data. So you dont need to overwrite it. You need some mechanism to create aggregation with previously aggregated data. also there should be some flag, which lets aggregate data of specific metric considering new data of 1 minute for supported metrics/1 hour for the metrics supported/1 day for the metrics supported/weekly or monthly aggregate for the supported one. Basically so that I can simulate what is happening. Also, the script should connect to the timescaledb docker image from task 1


## timescale_manager.py
Make the script executable:
chmod +x timescale_manager.py

To see which continuous aggregates are available:
./timescale_manager.py list

Refreshing Aggregates
Refresh all hourly aggregates for the last 30 days:
./timescale_manager.py refresh 1h

Refresh heart rate minute aggregates for a specific date range:
./timescale_manager.py refresh 1m --metric heart_rate --start-date "2023-01-01" --end-date "2023-01-31"

Refresh weekly SpO2 aggregates:
./timescale_manager.py refresh 1w --metric spo2

Querying Data
./timescale_manager.py query heart_rate 1 --start-date "2023-01-01" --end-date "2023-01-31"

Query raw heart rate data:
./timescale_manager.py query heart_rate 1 --start-date "2023-01-01" --end-date "2023-01-02" --raw

Query activity data with a limit:

./timescale_manager.py query activity 1 --start-date "2023-01-01" --end-date "2023-12-31" --limit 50

Talk about extensions


