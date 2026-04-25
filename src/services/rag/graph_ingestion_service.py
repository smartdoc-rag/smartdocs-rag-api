from typing import List, Optional
from langchain_core.documents import Document
from src.core.rag.llm_model import LLMModel
from src.core.rag.embedding_provider import get_embedding

# Optional imports for Neo4j
try:
    from langchain_neo4j import Neo4jVector
    NEO4JVECTOR_AVAILABLE = True
except ImportError:
    NEO4JVECTOR_AVAILABLE = False
    Neo4jVector = None

try:
    from langchain_experimental.graph_transformers import LLMGraphTransformer
    LLMGRAPH_AVAILABLE = True
except ImportError:
    LLMGRAPH_AVAILABLE = False
    LLMGraphTransformer = None

try:
    from src.core.rag.neo4j import neo4j_connect
    NEO4J_CONNECT_AVAILABLE = True
except ImportError:
    NEO4J_CONNECT_AVAILABLE = False
    neo4j_connect = None


def _patch_node_import_query():
    """Monkey-patch _get_node_import_query để dùng dynamic label thay vì
    apoc.create.addLabels (deprecated từ Neo4j 5.24).

    Áp dụng cho cả langchain_community và langchain_neo4j vì cả hai đều dùng
    cú pháp cũ.
    """
    import logging

    for module_name in (
        "langchain_community.graphs.neo4j_graph",
        "langchain_neo4j.graphs.neo4j_graph",
    ):
        try:
            mod = __import__(module_name, fromlist=["_get_node_import_query"])
            if not hasattr(mod, "_get_node_import_query"):
                continue

            base_label = getattr(mod, "BASE_ENTITY_LABEL", "__Entity__")
            include_docs = getattr(mod, "include_docs_query", "")

            def _make_patched(base_label=base_label, include_docs=include_docs):
                def _patched(baseEntityLabel: bool, include_source: bool) -> str:
                    if baseEntityLabel:
                        return (
                            f"{include_docs if include_source else ''}"
                            "UNWIND $data AS row "
                            f"MERGE (source:`{base_label}` {{id: row.id}}) "
                            "SET source += row.properties "
                            "SET source:$(row.type) "
                            f"{'MERGE (d)-[:MENTIONS]->(source) ' if include_source else ''}"
                            "RETURN distinct 'done' AS result"
                        )
                    else:
                        return (
                            f"{include_docs if include_source else ''}"
                            "UNWIND $data AS row "
                            "CALL apoc.merge.node([row.type], {id: row.id}, "
                            "row.properties, {}) YIELD node "
                            f"{'MERGE (d)-[:MENTIONS]->(node) ' if include_source else ''}"
                            "RETURN distinct 'done' AS result"
                        )
                return _patched

            mod._get_node_import_query = _make_patched()
            logging.getLogger(__name__).info(
                "Patched %s._get_node_import_query (dynamic labels)", module_name
            )
        except ImportError:
            pass


# Áp dụng patch ngay khi module được import
_patch_node_import_query()


class GraphIngestionService:
    def __init__(self):
        self.llm = LLMModel().get_ollama()
        self.embedding = get_embedding()
        self.graph = None
        self.neo4j_available = NEO4J_CONNECT_AVAILABLE and NEO4JVECTOR_AVAILABLE and LLMGRAPH_AVAILABLE

        if not self.neo4j_available:
            import logging
            logging.getLogger(__name__).warning(
                "Neo4j dependencies not available. Graph ingestion will be disabled."
            )
            return

        try:
            self.graph = neo4j_connect()
        except Exception as e:
            # Log warning but don't fail initialization
            import logging
            logging.getLogger(__name__).warning(f"Failed to connect to Neo4j: {e}")

    def create_vector_store(self,
                           documents: List[Document],
                           index_name: str = "chunk_index",
                           node_label: str = "Chunk",
                           text_node_property: str = "text",
                           embedding_node_property: str = "embedding") -> Optional[Neo4jVector]:
        """
        Tạo vector store trong Neo4j từ documents.
        """
        if not self.neo4j_available or self.graph is None or Neo4jVector is None:
            raise ValueError("Neo4j graph not available. Cannot create vector store.")

        # Get connection details from graph
        # Note: This assumes graph has _driver attribute
        try:
            uri = self.graph._driver._config.uri
            username = self.graph._driver._config.auth[0]
            password = self.graph._driver._config.auth[1]
        except AttributeError:
            raise ValueError("Neo4j graph driver configuration not accessible.")

        vector_store = Neo4jVector.from_documents(
            embedding=self.embedding,
            documents=documents,
            url=uri,
            username=username,
            password=password,
            database=username,
            index_name=index_name,
            node_label=node_label,
            text_node_property=text_node_property,
            embedding_node_property=embedding_node_property,
        )
        print(vector_store)
        return vector_store

    def create_graph_from_documents(self,
                                   documents: List[Document],
                                   baseEntityLabel: bool = True,
                                   include_source: bool = True) -> int:
        """
        Chuyển documents thành graph documents và thêm vào Neo4j.
        Trả về số graph documents đã thêm.
        """
        if not self.neo4j_available or self.graph is None or LLMGraphTransformer is None:
            raise ValueError("Neo4j graph not available. Cannot create graph.")

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
        """
        Ingest documents vào cả vector store và graph.
        Trả về thông tin kết quả.
        """
        result = {"vector_store_created": False, "graph_documents_count": 0}

        if not self.neo4j_available or self.graph is None:
            return {"error": "Neo4j not available", **result}

        try:
            # Tạo vector store
            vector_store = self.create_vector_store(documents, index_name=vector_index_name)
            result["vector_store_created"] = True
        except Exception as e:
            result["vector_error"] = str(e)

        try:
            # Tạo graph documents
            graph_count = self.create_graph_from_documents(documents)
            result["graph_documents_count"] = graph_count
        except Exception as e:
            result["graph_error"] = str(e)

        return result

    def clear_graph(self, confirm: bool = False) -> bool:
        """
        Xóa tất cả dữ liệu trong Neo4j graph.
        Chỉ thực hiện khi confirm=True.
        """
        if not confirm:
            return False

        if not self.neo4j_available or self.graph is None:
            return False

        try:
            # Xóa tất cả nodes và relationships
            self.graph.query("MATCH (n) DETACH DELETE n")
            return True
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to clear graph: {e}")
            return False