from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all routers
from app.routers.azm_router import router as azm_router
from app.routers.hr_router import router as heart_rate_router
from app.routers.spo2_router import router as spo2_router
from app.routers.hrv_router import router as hrv_router
from app.routers.br_router import router as breathing_rate_router
from app.routers.activity_router import router as activity_router
from app.routers.user_router import router as user_router
from app.routers.device_router import router as device_router

# Create FastAPI app
app = FastAPI(title="Fitbit Data API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(azm_router)
app.include_router(heart_rate_router)
app.include_router(spo2_router)
app.include_router(hrv_router)
app.include_router(breathing_rate_router)
app.include_router(activity_router)
app.include_router(user_router)
app.include_router(device_router)


# Root route
@app.get("/")
def read_root():
    return {"message": "Fitbit Data API is running", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint for container monitoring"""
    return {"status": "healthy"}
