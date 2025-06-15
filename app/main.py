from fastapi import FastAPI
from fastapi.security import HTTPBearer
from fastapi.openapi.utils import get_openapi

from app.core.all_models import *
from app.middlerware.auth import AuthMiddleware
from app.middlerware.cors import add_cors_middleware

from app.modules.auth.routes import router as auth_router
from app.modules.address.routes import router as address_router
from app.modules.activities.routes import router as activities_router
from app.modules.places.routes import router as places_router
from app.modules.storage.routes import router as image_router
from app.modules.service_provider.routes import router as service_provider_router
from app.modules.transport_route.routes import router as transport_route_router
from app.modules.transport_service.routes import router as transport_service_router
from app.modules.accomodation_service.routes import router as accomodation_service_router
from app.modules.plans.routes import router as plans_router

app = FastAPI()

security = HTTPBearer()
app.add_middleware(AuthMiddleware)
add_cors_middleware(app)

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(image_router, prefix="/image", tags=["Images"])
app.include_router(plans_router, prefix="/plans", tags=["Plans"])
app.include_router(address_router, prefix="/address", tags=["Address"])
app.include_router(activities_router, prefix="/activities", tags=["Activities"])
app.include_router(places_router, prefix="/places", tags=["Places"])
app.include_router(service_provider_router, prefix="/service-provider", tags=["Service Provider"])
app.include_router(transport_route_router, prefix="/transport-route", tags=["Transport Route"])
app.include_router(transport_service_router, prefix="/transport-service", tags=["Transport Service"])
app.include_router(accomodation_service_router, prefix="/accomodation-service", tags=["Accomodation Service"])

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Your API",
        version="1.0.0",
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
