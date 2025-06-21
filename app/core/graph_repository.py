from typing import Any, Dict, Generic, Optional, Type, TypeVar, Union
from neo4j import AsyncSession
from pydantic import BaseModel
from app.core.graph_schemas import BaseNode, BaseEdge

GraphSchemaType = TypeVar("GraphSchemaType", bound=Union[BaseNode, BaseEdge])

class BaseGraphRepository(Generic[GraphSchemaType]):
    def __init__(self, session: AsyncSession, model: Type[GraphSchemaType]):
        self.session = session
        self.model = model

        if issubclass(model, BaseNode):
            self.schema_type = "node"
        elif issubclass(model, BaseEdge):
            self.schema_type = "edge"
        else:
            raise TypeError("model must inherit from BaseNode or BaseEdge")

        # Set label from model class attribute, so you don't need to pass it again
        self.label = getattr(model, "label")
        if self.schema_type == "edge":
            self.start_label = model.start_model.label
            self.end_label = model.end_model.label
        else:
            self.start_label = None
            self.end_label = None

    async def ensure_constraints(self):
        if self.schema_type == "node":
            query = f"""
            CREATE CONSTRAINT IF NOT EXISTS
            FOR (n:{self.label}) REQUIRE n.id IS UNIQUE
            """
        else:
            query = f"""
            CREATE CONSTRAINT IF NOT EXISTS
            FOR ()-[r:{self.label}]-() REQUIRE r.id IS UNIQUE
            """
        await self.session.run(query)

    async def create(self, obj: GraphSchemaType) -> None:
        data = obj.model_dump(exclude={"start_model", "end_model"})

        if self.schema_type == "node":
            node_id = data.pop("id")

            await self.ensure_constraints()

            props_keys = ", ".join([f"{k}: ${k}" for k in data.keys()])
            query = f"""
            MERGE (n:{self.label} {{id: $node_id}})
            SET n += {{{props_keys}}}
            """
            await self.session.run(query, node_id=node_id, **data)

        else:  # edge
            start_id = data.pop("start_id")
            end_id = data.pop("end_id")
            edge_id = data.pop("id")
            data['start_label'] = self.start_label
            data['end_label'] = self.end_label

            await self.ensure_constraints()

            rel_props = {**data, "id": edge_id}
            props_str = ", ".join([f"{k}: ${k}" for k in rel_props.keys()])
            query = f"""
            MATCH (a:{self.start_label} {{id: $start_id}})
            MATCH (b:{self.end_label} {{id: $end_id}})
            MERGE (a)-[r:{self.label} {{id: $id}}]->(b)
            SET r += $rel_props
            """
            params = {
                "start_id": start_id,
                "end_id": end_id,
                "id": edge_id,
                "rel_props": rel_props,
                **rel_props
            }
            await self.session.run(query, **params)

    async def get(self, obj_id: int) -> Optional[GraphSchemaType]:
        if self.schema_type == "node":
            query = f"""
            MATCH (n:{self.label} {{id: $obj_id}})
            RETURN n
            """
            result = await self.session.run(query, obj_id=obj_id)
            record = await result.single()
            return self.model(**dict(record["n"])) if record else None
        else:
            query = f"""
            MATCH ()-[r:{self.label} {{id: $obj_id}}]-()
            RETURN r
            """
            result = await self.session.run(query, obj_id=obj_id)
            record = await result.single()
            return self.model(**dict(record["r"])) if record else None

    async def update(self, obj_id: int, update_data: Dict[str, Any]) -> bool:
        prefix = "n" if self.schema_type == "node" else "r"
        set_props = ", ".join([f"{prefix}.{k} = ${k}" for k in update_data.keys()])

        if self.schema_type == "node":
            query = f"""
            MATCH (n:{self.label} {{id: $obj_id}})
            SET {set_props}
            RETURN n
            """
        else:
            query = f"""
            MATCH ()-[r:{self.label} {{id: $obj_id}}]-()
            SET {set_props}
            RETURN r
            """
        result = await self.session.run(query, obj_id=obj_id, **update_data)
        return (await result.single()) is not None

    async def delete(self, obj_id: int) -> bool:
        if self.schema_type == "node":
            query = f"""
            MATCH (n:{self.label} {{id: $obj_id}})
            DETACH DELETE n
            """
        else:
            query = f"""
            MATCH ()-[r:{self.label} {{id: $obj_id}}]-()
            DELETE r
            """
        await self.session.run(query, obj_id=obj_id)
        return True
