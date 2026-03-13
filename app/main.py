from fastapi import FastAPI

from app.api.routes import admin, auth, mock_resources, users
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name,
              debug=settings.debug,
              version="1.0.0",
              description="Custom authentication and RBAC authorization service with JWT and mock business resources.",
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
