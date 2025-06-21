# app/core/graph_database.py
from neo4j import AsyncGraphDatabase
from app.core.config import settings

class GraphDB:
    def __init__(self):
        self._driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            database=settings.NEO4J_DATABASE,
        )

    def get_session(self):   # NOT async
        return self._driver.session()   # returns async context manager

    async def close(self):
        await self._driver.close()

graph_db = GraphDB()

async def get_graph_db():
    async with graph_db.get_session() as session:
        yield session
