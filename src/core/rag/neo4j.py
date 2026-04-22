from langchain_classic.graphs import Neo4jGraph
from src.settings import NEO4J_PASSWORD, NEO4J_URI, NEO4J_USERNAME


def neo4j_connect() -> Neo4jGraph:
    if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
        raise ValueError("NEO4J_URI, NEO4J_USERNAME, và NEO4J_PASSWORD không tồn tại")
    return Neo4jGraph(
        url=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
    )
