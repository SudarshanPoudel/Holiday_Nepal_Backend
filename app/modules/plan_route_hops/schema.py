from typing import Optional
from pydantic import BaseModel

from app.modules.transport_route.schema import TransportRouteRead

class PlanRouteHopCreate(BaseModel):
    plan_day_step_id: int
    index: int
    route_id: int
    destination_city_id: int


class PlanRouteHopRead(BaseModel):
    id: int
    plan_day_step_id: int
    index: int
    destination_city_id: int
    route: TransportRouteRead