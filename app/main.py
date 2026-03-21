from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, auth, mock_resources, users
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name,
              debug=settings.debug,
              version="1.0.0",
              description="Custom authentication and RBAC authorization service with JWT and mock business resources.",
              )

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
async def health():
    return {"status": "ok"}


@app.get('/')
async def root():
    return {'message': 'RBAC Auth Service is running'}
