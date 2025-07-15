# Task 2: Fitbit Health Data Visualization System

## Overview
This project builds a complete data flow model connecting a locally hosted TimescaleDB database with a modern web-based visualization dashboard. I've created a system that retrieves time-series health data from a Fitbit device, stores it in an optimized database, and presents it through an interactive visualization interface.

In order to execute this task, it's mandatory to complete Task 1 first, which involves setting up a TimescaleDB instance with synthetic data. I generated and loaded approximately 20 days worth of data in the previous task, which have been used in this task.

Mentionable, the solution in the task has been kept fairly simple as different complex tasks like advanced visualization, query optimization etc are part of the upcoming tasks.

## Architecture and Data Flow

The system follows a three-tier architecture with clear separation of concerns between data storage, application logic, and presentation layers:

```
┌───────────────┐     ┌───────────────────┐     ┌────────────────────┐     ┌───────────────┐
│  Data Source  │     │                   │     │                    │     │   Frontend    │
│  (Fitbit API/ │────▶│   TimescaleDB     │────▶│  FastAPI Backend   │────▶│   (React)     │
│  Synthetic)   │     │                   │     │                    │     │               │
└───────────────┘     └───────────────────┘     └────────────────────┘     └───────────────┘
                             │                           │                         │
                             │                           │                         │
                             ▼                           ▼                         ▼
                      ┌─────────────┐           ┌────────────────┐         ┌─────────────────┐
                      │ Time-series │           │ Data Processing │         │  Visualization  │
                      │  Data Store │           │ Query Building  │         │     Components  │
                      │             │           │ API Endpoints   │         │    (Recharts)   │
                      └─────────────┘           └────────────────┘         └─────────────────┘
```

### Data Flow Process

1. **Data Ingestion**: 
   - Health data is either generated synthetically or collected from Fitbit devices
   - Raw data is organized into appropriate time-series format

2. **Database Layer**: 
   - TimescaleDB stores time-series health metrics optimized for fast retrieval
   - Database schema organizes data by user, metric type, and timestamp
   - Hypertables provide efficient storage and query capabilities for time-series data

3. **API Layer**:
   - FastAPI backend exposes RESTful endpoints for each health metric
   - Processes query results and transforms data into API response format
   - Handles error cases and provides appropriate fallback mechanisms

4. **Presentation Layer**:
   - React frontend requests data via Axios HTTP client
   - Components manage state and handle loading/error conditions
   - Recharts library renders different visualization types based on the data


## Screenshots
<img width="1920" height="1080" alt="Image" src="https://github.com/user-attachments/assets/ff898334-e256-4676-94f5-7b9e4d8b244c" />

<img width="1920" height="1080" alt="Image" src="https://github.com/user-attachments/assets/5158fccb-8552-4dba-ba37-7a58d0a2a3ab" />

<img width="1920" height="1080" alt="Image" src="https://github.com/user-attachments/assets/c813e625-88a4-4c35-93ff-5db6477a02cf" />

<img width="1920" height="1080" alt="Image" src="https://github.com/user-attachments/assets/fb665852-6e6e-47e6-90a5-30eb52a87677" />

<img width="1920" height="1080" alt="Image" src="https://github.com/user-attachments/assets/a3bb477c-6aba-4a62-9db3-397d5569445c" />

<img width="1920" height="1080" alt="Image" src="https://github.com/user-attachments/assets/9c4440ce-c102-42ea-8240-ae05f10b80ac" />


## Technical Implementation

### Backend (FastAPI)

FastAPI has been chosen for the backend implementation because of its high performance, light weight, automatic documentation generation, and type checking capabilities. The backend serves as the intermediary between the TimescaleDB database and the frontend visualization layer.

psycopg2 has been used for database connection and management.

I decided to use raw SQL queries instead of an ORM for several reasons:
1. Better control over query optimization for time-series data
2. Ability to leverage TimescaleDB-specific functions and features
3. More transparent performance tuning
4. Direct mapping to the existing database schema

### Frontend (React)

The frontend is built with React along with the libraries:
- Material-UI for UI components
- Recharts for interactive data visualization
- Axios for API communication

I implemented multiple visualization components to display different types of health metrics:
- Line charts for trends over time (heart rate, SpO2, breathing rate)
- Bar charts for activity data
- Stacked charts for zone-based metrics
- Scatter plots for HRV frequency domain analysis

It is worth noting that, some of the metrics have millions of datapoints for this 20 days worth of data, to keep it simple, I decided to go with daily avg values of those metrics.

### Data Flow Process

1. User selects parameters (user_id, date range) in the frontend
2. React components make API calls to the backend
3. Backend constructs optimized SQL queries based on parameters
4. TimescaleDB executes queries and returns results
5. Backend processes and formats the data
6. Frontend renders visualizations based on the returned data

## Directory Structure

Task 2/
├── backend/
│   ├── app/
│   │   ├── init.py
│   │   ├── main.py           # FastAPI application entry point
│   │   ├── config.py         # Database configuration and settings
│   │   ├── database.py       # Database connection management
│   │   └── routers/          # API endpoint modules
│   │       ├── init.py
│   │       ├── users.py        # User management endpoints
│   │       ├── heart_rate.py   # Heart rate data endpoints
│   │       ├── spo2.py         # SpO2 data endpoints
│   │       ├── hrv.py          # HRV data endpoints
│   │       ├── breathing_rate.py # Breathing rate data endpoints
│   │       ├── azm.py          # Active Zone Minutes endpoints
│   │       └── activity.py     # Activity/steps data endpoints
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile            # Backend container configuration
├── frontend/
│   └── fitbit_visualizer/
│       ├── public/
│       │   ├── index.html
│       │   └── favicon.ico
│       ├── src/
│       │   ├── components/       # React visualization components
│       │   │   ├── UserSelector.js         # User selection component
│       │   │   ├── DateRangePicker.js      # Date range picker
│       │   │   ├── HeartRateChart.js       # Heart rate line chart
│       │   │   ├── HeartRateZoneChart.js   # Heart rate zones chart
│       │   │   ├── SpO2Chart.js            # SpO2 line chart
│       │   │   ├── HRVChart.js             # HRV trend chart
│       │   │   ├── HRVScatterChart.js      # HRV scatter plot
│       │   │   ├── BreathingRateChart.js   # Breathing rate line chart
│       │   │   ├── BreathingRateBarChart.js# Breathing rate bar chart
│       │   │   ├── AZMStackedChart.js      # Active Zone Minutes stacked chart
│       │   │   ├── AZMLineChart.js         # Active Zone Minutes line chart
│       │   │   ├── ActivityLineChart.js    # Activity line chart with trends
│       │   │   └── ActivityBarChart.js     # Activity bar chart
│       │   ├── services/           # API service modules
│       │   │   ├── api.js                # Base API configuration
│       │   │   ├── users_api.js          # User API calls
│       │   │   ├── heartRate_api.js      # Heart rate API calls
│       │   │   ├── spo2_api.js           # SpO2 API calls
│       │   │   ├── hrv_api.js            # HRV API calls
│       │   │   ├── breathingRate_api.js  # Breathing rate API calls
│       │   │   ├── azm_api.js            # Active Zone Minutes API calls
│       │   │   └── activity_api.js       # Activity API calls
│       │   ├── App.js              # Main React application component
│       │   ├── App.css             # Application styling
│       │   └── index.js            # React entry point
│       ├── package.json          # Node.js dependencies and scripts
│       ├── nginx.conf            # Nginx configuration for production
│       └── Dockerfile            # Frontend container configuration
├── docker-compose.yml      # Multi-container orchestration
└── README.md               # This documentation file


## API Endpoints

I implemented multiple API endpoints to support different health metrics and visualization needs:

### User Management
- `GET /api/users/get_all_users`: Returns all users in the system
- `GET /api/users/get_user/{user_id}`: Returns details of a specific user

### Heart Rate
- `GET /api/heart_rate/get_daily_avg_heart_rate_data`: Daily average heart rate with resting heart rate
- `GET /api/heart_rate/get_all_heart_rate_data`: All heart rate measurements within a timeframe
- `GET /api/heart_rate/get_heart_rate_zones_data`: Time spent in different heart rate zones

### SpO2 (Blood Oxygen)
- `GET /api/spo2/get_daily_avg_spo2_data`: Daily average blood oxygen saturation

### HRV (Heart Rate Variability)
- `GET /api/hrv/get_daily_avg_hrv_data`: Daily average HRV with RMSSD and frequency domain data

### Breathing Rate
- `GET /api/breathing_rate/get_all_breathing_rate_data`: Breathing rates for different sleep phases

### Active Zone Minutes
- `GET /api/azm/get_daily_avg_azm_data`: Daily average time spent in different activity zones

### Activity (Steps)
- `GET /api/activity/get_all_activity_data`: Daily step counts

Each endpoint accepts the following query parameters:
- `user_id`: The ID of the user whose data to retrieve
- `start_date`: Beginning of the time range (YYYY-MM-DD)
- `end_date`: End of the time range (YYYY-MM-DD)

## Design Decisions

### Backend Design Choices

1. **Raw SQL vs ORM**: I chose to use raw SQL queries directly rather than an ORM for several reasons:
   - Better performance with complex time-series queries
   - More direct control over query optimization
   - Ability to leverage TimescaleDB-specific functions
   - Simpler integration with the existing database schema

2. **FastAPI Framework**: I selected FastAPI because:
   - It offers superior performance compared to Flask or Django for API-only applications
   - Built-in parameter validation reduces error handling code
   - Automatic API documentation generation via Swagger UI
   - Native async support for handling concurrent requests

3. **Response Structure Standardization**: I implemented a consistent response format across all endpoints:
   ```json
   {
     "success": true,
     "parameters": {
       "user_id": 1,
       "start_date": "2024-01-01",
       "end_date": "2024-01-31"
     },
     "data_count": 31,
     "data": [...]
   }
   ```

4. In the config file, there's a variable called GMT6, which I initially used when the database was storing dates in GMT+6. I've since standardized on UTC in the database, but kept the variable for future flexibility.

### Frontend Design Choices

1. **Component-Based Architecture**: I separated each visualization into its own component for:
   - Better code organization and maintainability
   - Reusability across different views

2. **Visualizations**: I chose to implement multiple visualization types based on the nature of each metric:
   - Line charts for time-series trends (heart rate, SpO2)
   - Bar charts for daily activity metrics
   - Stacked charts for zone-based data (heart rate zones, active zone minutes)
   - Combined charts for complex metrics (HRV with multiple parameters)

3. **Daily Averages**: For metrics with high-frequency measurements, I chose to show daily averages rather than every single data point to:
   - Improve rendering performance
   - Enhance visual clarity
   - Reduce data transfer between backend and frontend

4. **Error Handling**: I implemented comprehensive error handling with:
   - Loading states for all data fetching operations
   - Fallback UI components when data is missing
   - Descriptive error messages for API failures
   - Graceful degradation when services are unavailable

## Error Handling & Fallback Mechanisms
I implemented several fallback mechanisms to ensure a robust user experience:

### Parameter Validation:
- If user_id is missing, the system defaults to user 1
- If start_date is missing, it defaults to "2024-01-01"
- If end_date is missing, it defaults to "2024-01-31"

### Empty Results Handling:
- When queries return no data, informative messages are displayed
- Visualization components have specific "no data" states

### Error Messages:
- Database connection errors are clearly communicated
- Invalid parameter types trigger helpful validation messages
- Network errors are displayed with retry options

### Data Quality Checks:
- NULL values in the database are properly handled
- Out-of-range values are filtered or flagged
- Inconsistent timestamps are normalized

## Running the Application

### Prerequisites
- Docker and Docker Compose installed
- TimescaleDB instance from Task 1 running with Fitbit data loaded

### Running with Docker

1. Start the TimescaleDB container from Task 1 (if not already running):
   ```
   cd "Task 1"
   docker compose up -d timescaledb
   ```

2. Launch the application using Docker Compose:
   ```
   cd "Task 2"
   docker compose up -d
   ```

3. Access the application:
   - Frontend: http://localhost
   - Backend API documentation: http://localhost:8000/docs

### Running Locally for Development
1. Start the TimescaleDB container from Task 1 (if not already running):
   ```
   cd "Task 1"
   docker compose up -d timescaledb
   ```

2. Run the backend:
   ```
   cd "Task 2/backend"
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

3. Run the frontend:
   ```
   cd "Task 2/frontend/fitbit_visualizer"
   npm install
   npm start
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API documentation: http://localhost:8000/docs

## Known Issues and Limitations
- **Heart Rate Zone Data**: I observed that heart rate zone data shows similar patterns throughout the month. This is not a problem with the ingestion process but rather an artifact of the synthetic data generation process.

- **Frontend Design Refinements**: There are some design improvements that could be made to the frontend. I prioritized functionality and a working data flow over design polish in this initial implementation.

- **Null Data Points**: Some null points are present in the visualizations. I deliberately maintained these to simulate real-world conditions where data might be missing or sensors might fail.

- **Daily Averages**: The frontend currently shows daily averages instead of every single data point to improve performance and clarity. This approach was chosen because the high volume of raw data points (potentially thousands per day) would make visualizations cluttered and slow to render. More advanced aggregation strategies will be implemented in Task 3.

- **Limited Data Volume**: Due to memory constraints during the data ingestion phase, I was only able to generate approximately 20 days of data. While this is sufficient for demonstration, a production system would typically handle much larger datasets.