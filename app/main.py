from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, auth, mock_resources, users
from app.core.config import get_settings
from app.core.rate_limiter import setup_rate_limiter, limiter


settings = get_settings()
app = FastAPI(title=settings.app_name,
              debug=settings.debug,
              version="1.0.0",
              description="Custom authentication and RBAC authorization service with JWT and mock business resources.",
              )

setup_rate_limiter(app)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(users.router, prefix=settings.api_v1_prefix)
app.include_router(admin.router, prefix=settings.api_v1_prefix)
app.include_router(mock_resources.router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["Health"])
@limiter.limit("10/minute")
async def health(request: Request):
    return {"status": "ok"}


@app.get('/')
@limiter.limit("5/minute")
async def root(request: Request):
    return {'message': 'RBAC Auth Service is running'}
