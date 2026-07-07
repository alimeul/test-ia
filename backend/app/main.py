from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.routers import defis, stats, tentatives


@asynccontextmanager
async def lifespan(application: FastAPI):
    init_db()
    yield


app = FastAPI(title="Wikidle API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(defis.router, prefix="/api")
app.include_router(tentatives.router, prefix="/api")
app.include_router(stats.router, prefix="/api")


@app.get("/")
async def root():
    return {"status": "ok"}
