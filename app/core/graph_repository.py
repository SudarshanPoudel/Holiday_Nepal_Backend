from typing import Any, Dict, Optional, Tuple, Type, List, TypeVar, Generic, ClassVar, Set
from neo4j import AsyncSession
from pydantic import BaseModel

from app.core.graph_schemas import BaseEdge, BaseNode

NodeType = TypeVar("NodeType", bound=BaseNode)

class BaseGraphRepository(Generic[NodeType]):
    def __init__(self, session: AsyncSession, model: Type[NodeType]):
        self.session = session
        self.model = model
        self.label = getattr(model, "label")
        self._constraints_ensured = False

    @classmethod
    async def create_repository(cls, session: AsyncSession, model: Type[NodeType]) -> "BaseGraphRepository[NodeType]":
        """Factory method to create repository with constraints ensured"""
        repo = cls(session, model)
        await repo.ensure_constraints()
        repo._constraints_ensured = True
        return repo

    async def _ensure_constraints_if_needed(self):
        """Ensure constraints are created (called automatically on first use)"""
        if not self._constraints_ensured:
            await self.ensure_constraints()
            self._constraints_ensured = True

    async def ensure_constraints(self):
        """Ensure uniqueness constraints for the node"""
        query = f"""
        CREATE CONSTRAINT IF NOT EXISTS
        FOR (n:{self.label}) REQUIRE n.id IS UNIQUE
        """
        await self.session.run(query)

    async def create(self, obj: NodeType) -> None:
        """Create a new node"""
        await self._ensure_constraints_if_needed()
        
        data = obj.model_dump()
        node_id = data.pop("id")

        props_keys = ", ".join([f"{k}: ${k}" for k in data.keys()])
        query = f"""
        MERGE (n:{self.label} {{id: $node_id}})
        SET n += {{{props_keys}}}
        """
        await self.session.run(query, node_id=node_id, **data)

    async def get(self, obj_id: int) -> Optional[NodeType]:
        """Get a node by ID"""
        query = f"""
        MATCH (n:{self.label} {{id: $obj_id}})
        RETURN n
        """
        result = await self.session.run(query, obj_id=obj_id)
        record = await result.single()
        return self.model(**dict(record["n"])) if record else None

    async def update(self, obj: NodeType) -> bool:
        """Update a node"""
        data = obj.model_dump()
        obj_id = data.pop("id")
        
        if not data:  # No fields to update besides id
            return True
            
        set_props = ", ".join([f"n.{k} = ${k}" for k in data.keys()])
        
        query = f"""
        MATCH (n:{self.label} {{id: $obj_id}})
        SET {set_props}
        RETURN n
        """
        result = await self.session.run(query, obj_id=obj_id, **data)
        return (await result.single()) is not None

    async def delete(self, obj_id: int, cascade: bool = True, sequential: bool = True) -> bool:
        """Delete a node with options to cascade and follow sequential child links"""
        if cascade:
            return await self._delete_with_cascade(obj_id, sequential)
        else:
            return await self._delete_simple(obj_id)


    async def _delete_simple(self, obj_id: int) -> bool:
        """Delete a node and all its relationships"""
        query = f"""
        MATCH (n:{self.label} {{id: $obj_id}})
        DETACH DELETE n
        """
        await self.session.run(query, obj_id=obj_id)
        return True


    async def _delete_with_cascade(self, obj_id: int, sequential: bool) -> bool:
        """Delete a node and cascade deletion to all child nodes recursively"""
        child_relationships_to_delete = await self.get_all_child_relationships(obj_id, sequential)

        for child_node_id, child_label in child_relationships_to_delete:
            await self._delete_node_by_id_and_label(child_node_id, child_label)

        await self._delete_simple(obj_id)
        return True


    async def get_all_child_relationships(self, node_id: int, sequential: bool) -> List[Tuple[int, str]]:
        """
        Recursively get all child nodes that should be deleted, including sequential links.
        Returns a list of (node_id, label) tuples.
        """
        child_relationships: List[Tuple[int, str]] = []

        # Handle normal child_relationships relationships
        if hasattr(self.model, 'child_relationships') and self.model.child_relationships:
            child_rels: Dict[str, str] = self.model.child_relationships  # rel_name -> label
            for rel_name, child_label in child_rels.items():
                query = f"""
                MATCH (parent:{self.label} {{id: $node_id}})-[:{rel_name}]->(child:{child_label})
                RETURN DISTINCT child.id AS child_id
                """
                result = await self.session.run(query, node_id=node_id)
                records = await result.data()
                for record in records:
                    child_id = record["child_id"]
                    child_relationships.append((child_id, child_label))

                    child_model = self._get_model_by_label(child_label)
                    if child_model:
                        child_repo = BaseGraphRepository(self.session, child_model)
                        grandchildren = await child_repo.get_all_child_relationships(child_id, sequential)
                        child_relationships.extend(grandchildren)
            print(f"DEBUG: child_relationships: {child_relationships} Found For Node {self.label} {node_id}")
        # Handle sequential chains if specified
        if sequential and hasattr(self.model, 'sequential_child_relationships'):
            for rel_name, target_label in self.model.sequential_child_relationships.items():
                next_id = node_id
                while next_id:
                    query = f"""
                    MATCH (current:{self.label} {{id: $current_id}})-[:{rel_name}]->(next:{target_label})
                    RETURN next.id AS next_id
                    """
                    result = await self.session.run(query, current_id=next_id)
                    record = await result.single()
                    if record and record["next_id"]:
                        next_id = record["next_id"]
                        child_relationships.append((next_id, target_label))
                    else:
                        break
            print(f"DEBUG: after sequential_child_relationships: {child_relationships} Found For Node {self.label} {node_id}")
        return child_relationships


    def _get_model_by_label(self, label: str) -> Optional[Type[BaseNode]]:
        from app.core.all_graph_models import label_to_model
        return label_to_model(label)

    async def _delete_node_by_id_and_label(self, node_id: int, label: str) -> None:
        """Delete a node by ID and label"""
        query = f"""
        MATCH (n:{label} {{id: $node_id}})
        DETACH DELETE n
        """
        await self.session.run(query, node_id=node_id)

    async def get_children(self, node_id: int, child_type: Optional[str] = None) -> List[Tuple[int, str]]:
        """Get direct children of a node
        
        Returns:
            List of tuples (child_id, child_label)
        """
        children = []
        
        if hasattr(self.model, 'child_relationships') and self.model.child_relationships:
            child_labels_to_check = self.model.child_relationships
            
            if child_type:
                # Filter to specific child type
                child_labels_to_check = [
                    child_label for child_label in child_labels_to_check
                    if child_label == child_type
                ]
            
            for child_label in child_labels_to_check:
                query = f"""
                MATCH (parent:{self.label} {{id: $node_id}})-[r]->(child:{child_label})
                RETURN DISTINCT child.id as child_id
                """
                
                result = await self.session.run(query, node_id=node_id)
                records = await result.data()
                
                for record in records:
                    children.append((record["child_id"], child_label))
        
        return children

    async def add_edge(self, edge_instance: BaseEdge) -> None:
        """Add an edge - works for both source and target directions"""
        # Check if this repository's node type can be either source or target
        can_be_source = edge_instance.__class__.source_model == self.model
        can_be_target = edge_instance.__class__.target_model == self.model
        
        if not (can_be_source or can_be_target):
            raise ValueError(
                f"Edge type {edge_instance.__class__.label} cannot connect to {self.model.label}. "
                f"Expected source: {edge_instance.__class__.source_model.label} or "
                f"target: {edge_instance.__class__.target_model.label}"
            )
        
        # Ensure edge constraint
        await self._ensure_edge_constraint(edge_instance.__class__)
        
        source_label = edge_instance.__class__.source_model.label
        target_label = edge_instance.__class__.target_model.label
        edge_label = edge_instance.__class__.label
        
        # Prepare edge properties - exclude source_id, target_id, and id from properties
        edge_props = edge_instance.model_dump()
        source_id = edge_props.pop("source_id")
        target_id = edge_props.pop("target_id") 
        edge_id = edge_props.pop("id")
        
        # Build the SET clause for edge properties
        if edge_props:
            set_props = ", ".join([f"r.{k} = ${k}" for k in edge_props.keys()])
            set_clause = f"SET {set_props}"
        else:
            set_clause = ""
        
        query = f"""
        MATCH (source:{source_label} {{id: $source_id}})
        MATCH (target:{target_label} {{id: $target_id}})
        MERGE (source)-[r:{edge_label} {{id: $edge_id}}]->(target)
        {set_clause}
        """
        
        await self.session.run(
            query,
            source_id=source_id,
            target_id=target_id,
            edge_id=edge_id,
            **edge_props
        )

    async def delete_edge(self, edge_type: Type[BaseEdge], edge_id: str) -> bool:
        """Delete an edge by its ID"""
        edge_label = edge_type.label
        
        query = f"""
        MATCH ()-[r:{edge_label} {{id: $edge_id}}]-()
        DELETE r
        RETURN COUNT(r) as deleted_count
        """
        
        result = await self.session.run(query, edge_id=edge_id)
        record = await result.single()
        return record["deleted_count"] > 0 if record else False

    async def update_edge(self, edge_instance: BaseEdge) -> bool:
        """Update an edge's properties and potentially its connections"""
        # Check if this repository's node type can be either source or target
        can_be_source = edge_instance.__class__.source_model == self.model
        can_be_target = edge_instance.__class__.target_model == self.model
        
        if not (can_be_source or can_be_target):
            raise ValueError(
                f"Edge type {edge_instance.__class__.label} cannot connect to {self.model.label}. "
                f"Expected source: {edge_instance.__class__.source_model.label} or "
                f"target: {edge_instance.__class__.target_model.label}"
            )
        
        edge_label = edge_instance.__class__.label
        
        # Get current edge to check if source/target changed
        current_edge = await self.get_edge(edge_instance.__class__, edge_instance.id)
        if not current_edge:
            return False  # Edge doesn't exist
        
        # Check if source or target changed
        source_changed = current_edge.source_id != edge_instance.source_id
        target_changed = current_edge.target_id != edge_instance.target_id
        
        if source_changed or target_changed:
            # Delete the old edge and create a new one
            await self.delete_edge(edge_instance.__class__, edge_instance.id)
            await self.add_edge(edge_instance)
        else:
            # Just update properties
            edge_props = edge_instance.model_dump()
            # Remove source_id, target_id, and id from properties to set
            update_props = {k: v for k, v in edge_props.items() if k not in ['source_id', 'target_id', 'id']}
            
            if update_props:  # Only update if there are properties to update
                set_props = ", ".join([f"r.{k} = ${k}" for k in update_props.keys()])
                
                query = f"""
                MATCH ()-[r:{edge_label} {{id: $edge_id}}]-()
                SET {set_props}
                RETURN r
                """
                
                result = await self.session.run(query, edge_id=edge_instance.id, **update_props)
                return (await result.single()) is not None
        
        return True

    async def get_edge(self, edge_type: Type[BaseEdge], edge_id: str) -> Optional[BaseEdge]:
        """Get an edge by its ID"""
        edge_label = edge_type.label
        
        query = f"""
        MATCH ()-[r:{edge_label} {{id: $edge_id}}]-()
        RETURN r
        """
        
        result = await self.session.run(query, edge_id=edge_id)
        record = await result.single()
        return edge_type(**dict(record["r"])) if record else None

    async def get_edges(self, edge_type: Type[BaseEdge], node_id: int, direction: str = "both") -> List[BaseEdge]:
        """Get edges connected to a node"""
        if direction not in {"outgoing", "incoming", "both"}:
            raise ValueError("direction must be one of 'outgoing', 'incoming', or 'both'")
            
        edge_label = edge_type.label
        
        if direction == "outgoing":
            query = f"""
            MATCH (n:{self.label} {{id: $node_id}})-[r:{edge_label}]->()
            RETURN r
            """
        elif direction == "incoming":
            query = f"""
            MATCH ()-[r:{edge_label}]->(n:{self.label} {{id: $node_id}})
            RETURN r
            """
        else:  # both
            query = f"""
            MATCH (n:{self.label} {{id: $node_id}})
            MATCH (n)-[r:{edge_label}]-()
            RETURN r
            """
        
        result = await self.session.run(query, node_id=node_id)
        records = await result.data()
        return [edge_type(**dict(record["r"])) for record in records]

    async def clear_edges(self, node_id: int, edge_type: Optional[Type[BaseEdge]] = None, direction: str = "both") -> None:
        """Clear edges from a node"""
        if direction not in {"outgoing", "incoming", "both"}:
            raise ValueError("direction must be one of 'outgoing', 'incoming', or 'both'")

        edge_label = edge_type.label if edge_type else ""
        rel_pattern = f"[r:{edge_label}]" if edge_type else "[r]"

        if direction == "outgoing":
            query = f"""
            MATCH (n:{self.label} {{id: $node_id}})-{rel_pattern}->()
            DELETE r
            """
        elif direction == "incoming":
            query = f"""
            MATCH ()-{rel_pattern}->(n:{self.label} {{id: $node_id}})
            DELETE r
            """
        else:  # both
            query = f"""
            MATCH (n:{self.label} {{id: $node_id}})-{rel_pattern}-()
            DELETE r
            """

        await self.session.run(query, node_id=node_id)
   
    async def shortest_path(
        self, 
        start_node_id: int, 
        end_node_id: int, 
        edge_type: Type[BaseEdge], 
        weight_property: str,
        directed: bool = False,
    ) -> List[tuple[int, int]]:
        """
        Find the weighted shortest path using GDS Dijkstra between two nodes.
        Returns list of (edge_id, next_node_id) for each hop along the path.
        """
        edge_label = edge_type.label
        orientation = "NATURAL" if directed else "UNDIRECTED"

        # Ensure default in-memory graph exists (once per session)
        await self.ensure_graph_exists(edge_label, weight_property, orientation)

        # Step 1: Run GDS Dijkstra to get node path
        query = f"""
        MATCH (start:{self.label} {{id: $start_node_id}}), (end:{self.label} {{id: $end_node_id}})
        CALL gds.shortestPath.dijkstra.stream(
            'defaultGraph',
            {{
                sourceNode: id(start),
                targetNode: id(end),
                relationshipWeightProperty: '{weight_property}'
            }}
        )
        YIELD nodeIds
        RETURN [nodeId IN nodeIds | gds.util.asNode(nodeId).id] AS nodePath
        """

        result = await self.session.run(
            query,
            start_node_id=start_node_id,
            end_node_id=end_node_id,
        )
        record = await result.single()
        if not record or len(record["nodePath"]) < 2:
            return []

        node_path = record["nodePath"]

        # Step 2: Fetch edge IDs between each consecutive pair of nodes
        query_edges = f"""
        UNWIND range(0, size($nodes) - 2) AS i
        MATCH (a:{self.label} {{id: $nodes[i]}})-[r:{edge_label}]->(b:{self.label} {{id: $nodes[i+1]}})
        RETURN r.id AS edgeId, b.id AS nodeId
        ORDER BY i
        """

        result_edges = await self.session.run(query_edges, nodes=node_path)
        return [(record["edgeId"], record["nodeId"]) async for record in result_edges]

    async def ensure_graph_exists(self, edge_label: str, weight_property: str, orientation: str):
        check_query = "CALL gds.graph.exists('defaultGraph') YIELD exists RETURN exists"
        result = await self.session.run(check_query)
        record = await result.single()
        if not record["exists"]:
            # Project all nodes and edges of the given type with the weight
            project_query = f"""
            CALL gds.graph.project(
                'defaultGraph',
                '{self.label}',
                {{
                    {edge_label}: {{
                        type: '{edge_label}',
                        properties: ['{weight_property}'],
                        orientation: '{orientation}'
                    }}
                }}
            )
            """
            await self.session.run(project_query)


    async def _ensure_edge_constraint(self, edge_type: Type[BaseEdge]):
        """Ensure uniqueness constraint for an edge type"""
        edge_label = edge_type.label
        query = f"""
        CREATE CONSTRAINT IF NOT EXISTS
        FOR ()-[r:{edge_label}]-() REQUIRE r.id IS UNIQUE
        """
        await self.session.run(query)