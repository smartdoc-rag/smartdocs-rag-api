import logging
from typing import List, Optional
from langchain_core.documents import Document
from langchain_neo4j import Neo4jVector
from langchain_experimental.graph_transformers import LLMGraphTransformer

from src.settings import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE
from src.core.rag.llm_model import LLMModel
from src.core.rag.embedding_provider import get_embedding
from src.core.rag.neo4j import neo4j_connect


class GraphIngestionService:
    def __init__(self):
        self.llm = LLMModel().get_ollama()
        self.embedding = get_embedding()
        self.graph = None
        try:
            self.graph = neo4j_connect()
        except Exception as e:
            logging.getLogger(__name__).warning(f"Failed to connect to Neo4j: {e}")

    def create_vector_store(self,
                            documents: List[Document],
                            index_name: str = "chunk_index",
                            node_label: str = "Chunk",
                            text_node_property: str = "text",
                            embedding_node_property: str = "embedding") -> Optional[Neo4jVector]:
        vector_store = Neo4jVector.from_documents(
            embedding=self.embedding,
            documents=documents,
            url=NEO4J_URI,
            username=NEO4J_USERNAME,
            password=NEO4J_PASSWORD,
            database=NEO4J_DATABASE,
            index_name=index_name,
            node_label=node_label,
            text_node_property=text_node_property,
            embedding_node_property=embedding_node_property,
        )
        return vector_store

    def create_graph_from_documents(self,
                                    documents: List[Document],
                                    baseEntityLabel: bool = True,
                                    include_source: bool = True) -> int:
        llm_transformer = LLMGraphTransformer(llm=self.llm)
        graph_documents = llm_transformer.convert_to_graph_documents(documents)

        self.graph.add_graph_documents(
            graph_documents,
            baseEntityLabel=baseEntityLabel,
            include_source=include_source
        )
        return len(graph_documents)

    def hybrid_ingest(self,
                      documents: List[Document],
                      vector_index_name: str = "chunk_index") -> dict:
        result = {"vector_store_created": False, "graph_documents_count": 0}
        try:
            self.create_vector_store(documents, index_name=vector_index_name)
            result["vector_store_created"] = True
        except Exception as e:
            result["vector_error"] = str(e)

        try:
            graph_count = self.create_graph_from_documents(documents)
            result["graph_documents_count"] = graph_count
        except Exception as e:
            result["graph_error"] = str(e)

        return result

    def clear_graph(self, confirm: bool = False) -> bool:
        if not confirm:
            return False

        try:
            self.graph.query("MATCH (n) DETACH DELETE n")
            return True
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to clear graph: {e}")
            return False
