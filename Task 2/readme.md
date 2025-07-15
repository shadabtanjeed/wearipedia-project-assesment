- In the config file, there is a variable called GMT6, which is used in all other api endpoints. Initially the db was storing the date in GMT6, but now it is storing in UTC. This variable is not used anymore, but I have kept it for future use if needed.
- Talk about why using  SQL query instead of ORM
- List the fallback mechanism used in this task

Knows Issues:


To run:
Start the timescaledb docker from task 1 directory firsr:
docker compose up -d timescaledb

cd "Task 2"
cd backend
uvicorn app.main:app --reload

You can view the documentation here:
http://127.0.0.1:8000/docs