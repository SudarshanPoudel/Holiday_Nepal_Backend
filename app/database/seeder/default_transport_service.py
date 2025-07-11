from sqlalchemy import insert, select
from app.core.all_models import TransportService, TransportServiceRouteSegment, City, TransportRoute, Image
from app.modules.transport_service.models import transport_service_images
from app.database.seeder.utils import get_file_path, load_data
from app.modules.transport_service.schema import TransportServiceCategoryEnum
from app.modules.transport_route.schema import RouteCategoryEnum
from app.modules.storage.schema import ImageCategoryEnum

from app.modules.storage.service import StorageService
from app.utils.image_utils import validate_and_process_image

# Import graph-related classes (adjust imports based on your actual structure)
from app.modules.transport_service.graph import (
    TransportServiceNode,
    TransportServiceCityEdge,
    TransportServiceTransportRouteHopEdge,
    TransportServiceGraphRepository,
    TransportServiceRouteHopGraphRepository
)
from app.modules.transport_service.graph import (
    TransportServiceRouteHopNode,
    TransportServiceRouteHopCityEdge,
    TransportServiceRouteHopTransportServiceRouteHopEdge
)


async def seed_default_transport_services(db, graph_db):
    # Initialize graph repositories
    graph_repository = TransportServiceGraphRepository(graph_db)
    route_hop_graph_repository = TransportServiceRouteHopGraphRepository(graph_db)
    
    transport_services = load_data("files/default_transport_services.json")
    for entry in transport_services:
        route_ids = []
        total_distance = 0
        total_time = 0

        for segment in entry["segments"]:
            start = await db.scalar(select(City).where(City.name == segment["start"]))
            end = await db.scalar(select(City).where(City.name == segment["end"]))

            if not start or not end:
                print(f"Invalid city: {segment}")
                continue

            route = await db.scalar(select(TransportRoute).where(
                TransportRoute.start_city_id == start.id,
                TransportRoute.end_city_id == end.id
            ))

            if not route:
                route = await db.scalar(select(TransportRoute).where(
                    TransportRoute.start_city_id == end.id,
                    TransportRoute.end_city_id == start.id
                ))
                if not route:
                    continue

            route_ids.append(route.id)
            total_distance += route.distance
            total_time += route.average_duration or 0

        start_mun = await db.scalar(select(City).where(City.name == entry["segments"][0]["start"]))
        end_mun = await db.scalar(select(City).where(City.name == entry["segments"][-1]["end"]))

        if not start_mun or not end_mun:
            continue
        
        new_service = TransportService(
            description=entry["description"],
            start_city_id=start_mun.id,
            end_city_id=end_mun.id,
            route_category=RouteCategoryEnum(entry["route_category"]),
            transport_category=TransportServiceCategoryEnum(entry["transport_category"]),
            total_distance=total_distance,
            average_duration=total_time,
            cost=entry.get("cost")
        )
        db.add(new_service)
        await db.flush()

        # Create graph node for transport service
        await graph_repository.create(
            TransportServiceNode(
                id=new_service.id,
                start_city_id=start_mun.id,
                end_city_id=end_mun.id,
                route_category=entry["route_category"],
                transport_category=entry["transport_category"],
                total_distance=total_distance,
                average_duration=total_time,
                cost=entry.get("cost")
            )
        )

        # Create edge between transport service and start city
        await graph_repository.add_edge(
            TransportServiceCityEdge(
                source_id=new_service.id,
                target_id=start_mun.id
            )
        )

        # Create route segments and their graph representations
        segments = []
        for idx, route_id in enumerate(route_ids):
            segment = TransportServiceRouteSegment(
                service_id=new_service.id,
                route_id=route_id,
                index=idx
            )
            db.add(segment)
            await db.flush()
            segments.append(segment)

        # Create graph nodes and edges for route segments
        last_segment = None
        for i, segment in enumerate(segments):
            route = await db.scalar(select(TransportRoute).where(TransportRoute.id == segment.route_id))
            
            # Create route hop node
            await route_hop_graph_repository.create(
                TransportServiceRouteHopNode(
                    id=segment.id, 
                    route_id=segment.route_id
                )
            )
            
            # Create edge from route hop to end city
            await route_hop_graph_repository.add_edge(
                TransportServiceRouteHopCityEdge(
                    source_id=segment.id, 
                    target_id=route.end_city_id
                )
            )
            
            # Create edges between segments
            if last_segment is None:
                # First segment - connect to transport service
                await graph_repository.add_edge(
                    TransportServiceTransportRouteHopEdge(
                        source_id=new_service.id,
                        target_id=segment.id,
                    )
                )
            else:
                # Connect to previous segment
                await route_hop_graph_repository.add_edge(
                    TransportServiceRouteHopTransportServiceRouteHopEdge(
                        source_id=last_segment.id,
                        target_id=segment.id,
                    )
                )
            
            last_segment = segment

        # Handle images
        transport_images = []
        for path in entry.get("images", []):
            file_path = get_file_path(f"../../../seeder-images/transport/{path}")
            key = f"services/{StorageService.generate_unique_key('webp')}"
            existing = await db.scalar(select(Image).where(Image.key == key))
            if existing:
                transport_images.append(existing)
                continue
            
            try:
                with open(file_path, "rb") as f:
                    content = f.read()
                content = validate_and_process_image(content, resize_to=(1080, 720))
                s3_service = StorageService()
                await s3_service.upload_file(key, content, "image/webp")

                image = Image(key=key, category=ImageCategoryEnum.services)
                db.add(image)
                await db.flush()
                transport_images.append(image)
            except Exception as e:
                print(f"Error processing image {path}: {e}")
                continue

        # Associate images with transport service
        for image in transport_images:
            existing = await db.scalar(
                select(transport_service_images).where(
                    transport_service_images.c.transport_service_id == new_service.id, 
                    transport_service_images.c.image_id == image.id
                )
            )
            if existing:
                continue
            await db.execute(
                insert(transport_service_images).values(
                    transport_service_id=new_service.id, 
                    image_id=image.id
                )
            )

    await db.commit()
    print("Seeder: Transport services seeded with graph data.")