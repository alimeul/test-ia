from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import defis

app = FastAPI(title="Wikidle API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(defis.router, prefix="/api")


@app.get("/")
async def root():
    return {"status": "ok"}
