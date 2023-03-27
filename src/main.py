from fastapi_users import FastAPIUsers

from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from auth.auth import auth_backend
from database import User
from auth.manager import get_user_manager
from auth.schemas import UserRead, UserCreate
from redis import asyncio as aioredis
from operations.router import router as router_operations
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from tasks.router import router as tasks_router
from fastapi.middleware.cors import CORSMiddleware
from pages.router import router as router_pages

app = FastAPI(
    title="Trading App"
)
app.mount("/static", StaticFiles(directory="static"), name="static")
fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

current_user = fastapi_users.current_user()

app.include_router(router_operations)
app.include_router(tasks_router)
app.include_router(router_pages)
origins = [
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "DELETE", "PATCH", "PUT"],
    allow_headers=["Content-Type", "Set-Cookie", "Access-Control-Allow-Headers", "Access-Control-Allow-Origin",
                   "Authorization"],
)


@app.get("/protected-route")
def protected_route(user: User = Depends(current_user)):
    return f"Hello, {user.username}"


@app.get("/unprotected-route")
def unprotected_route():
    return f"Hello, anonym"


@app.on_event("startup")
async def startup_event():
    redis = aioredis.from_url("redis://redis:5370", encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
