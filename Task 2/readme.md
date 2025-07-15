- In the config file, there is a variable called GMT6, which is used in all other api endpoints. Initially the db was storing the date in GMT6, but now it is storing in UTC. This variable is not used anymore, but I have kept it for future use if needed.
- Talk about why using  SQL query instead of ORM
- List the fallback mechanism used in this task

- the front end shows daily avg instead of every single data point as the no of data points is too high.Aggregations are not done as it is the task for next task.

Knows Issues:
- For some reason heart rate zone has same data through out the monnth. This is not a problem in data ingestion, rather it is a created due to the manipulation done on synthetically generated data. 
- In the front end, there are some design fix required, but since having a working front end was the priority, it has been skipped for now.
- There are some null points present in the data to simulate the real world scenario.


To run:
Start the timescaledb docker from task 1 directory firsr:
docker compose up -d timescaledb

cd "Task 2"
cd backend
uvicorn app.main:app --reload

You can view the documentation here:
http://127.0.0.1:8000/docs