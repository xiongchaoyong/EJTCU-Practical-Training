import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from scheduler import start_scheduler, stop_scheduler
from routes.sources import router as sources_router
from routes.fetch import router as fetch_router
from routes.latest import router as latest_router
from routes.settings import router as settings_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")
    init_db()
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("Application stopped.")


app = FastAPI(
    title="每日新闻聚合器",
    description="RSS 新闻抓取 + AI 总结 + Markdown 日报生成",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sources_router)
app.include_router(fetch_router)
app.include_router(latest_router)
app.include_router(settings_router)


@app.get("/")
def root():
    return {"message": "每日新闻聚合器 API", "version": "1.0.0"}
