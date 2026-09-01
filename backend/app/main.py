from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.errors import AppError, app_error_handler, unhandled_exception_handler
from app.routers import analytics, categories, groups, health, invites, line_items, me, receipts, split

app = FastAPI(title="Receipt Splitter API")

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(health.router)
app.include_router(me.router)
app.include_router(groups.router)
app.include_router(invites.router)
app.include_router(categories.router)
app.include_router(receipts.router)
app.include_router(line_items.router)
app.include_router(split.router)
app.include_router(analytics.router)
