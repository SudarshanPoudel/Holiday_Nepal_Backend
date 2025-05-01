from fastapi import FastAPI

from app.modules.auth.routes import router as auth_router
from app.modules.address.routes import router as address_router
from app.middlerware.auth import AuthMiddleware
from app.middlerware.cors import add_cors_middleware
from app.utils.scheduler import start_scheduler

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
app = FastAPI()

security = HTTPBearer()
app.add_middleware(AuthMiddleware)
add_cors_middleware(app)

@app.on_event("startup")
async def on_startup():
    start_scheduler()

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(address_router, prefix="/address", tags=["Address"])

from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Your API",
        version="1.0.0",
        description="Your API description",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
