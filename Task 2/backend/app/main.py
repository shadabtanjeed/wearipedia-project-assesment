from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from .routers.azm_router import router as azm_router

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


# Root route
@app.get("/")
def read_root():
    return {"message": "Fitbit Data API is running"}
