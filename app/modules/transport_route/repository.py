from app.core.repository import BaseRepository
from app.modules.transport_route.models import TransportRoute
from app.modules.transport_route.schema import TransportRouteCreate

class TransportRouteRepository(BaseRepository[TransportRoute, TransportRouteCreate]):
    def __init__(self, db):
        super().__init__(TransportRoute, db)

    async def get_from_city(self, city_id: int, load_relations: list[str] = None):
        start_with = await self.get_all_filtered(filters={"start_city_id": city_id}, load_relations=load_relations)
        end_with = await self.get_all_filtered(filters={"end_city_id": city_id}, load_relations=load_relations)
        
        all_data = list(set(start_with + end_with))
        return all_data
