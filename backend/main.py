from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import estimates

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AEONID Agent Brain OS", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(estimates.router, prefix="/estimates", tags=["estimates"])

@app.get("/health")
def health():
    return {"status": "ok"}
