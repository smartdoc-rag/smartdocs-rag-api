from typing import Optional, List, Tuple
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.prompts import PromptTemplate
from src.core.rag.llm_model import LLMModel
from src.core.rag.prompt import PROMPT_VI, PROMPT_EN, _is_vietnamese

# Optional imports for Neo4j
try:
    from langchain_neo4j import GraphCypherQAChain
    GRAPHCYPHER_AVAILABLE = True
except ImportError:
    try:
        from langchain_classic import GraphCypherQAChain
        GRAPHCYPHER_AVAILABLE = True
    except ImportError:
        GRAPHCYPHER_AVAILABLE = False
        GraphCypherQAChain = None  # type: ignore

try:
    from src.core.rag.neo4j import neo4j_connect
    NEO4J_CONNECT_AVAILABLE = True
except ImportError:
    NEO4J_CONNECT_AVAILABLE = False
    neo4j_connect = None  # type: ignore


class GraphRAGService:
    def __init__(self):
        self.llm = LLMModel().get_ollama()
        self.graph = None
        self.graph_error = None
        self.neo4j_available = GRAPHCYPHER_AVAILABLE and NEO4J_CONNECT_AVAILABLE

        if not self.neo4j_available:
            import logging
            logging.getLogger(__name__).warning(
                "Neo4j dependencies not available. GraphRAG will be disabled."
            )
            return

        try:
            self.graph = neo4j_connect()
        except Exception as e:
            self.graph_error = str(e)
            # Log warning
            import logging
            logging.getLogger(__name__).warning(f"Failed to connect to Neo4j: {e}")

    def _get_cypher_prompt(self, selected_file_ids: Optional[List[int]] = None) -> PromptTemplate:
        """Tạo prompt cho Cypher generation"""
        file_filter = ""
        if selected_file_ids:
            file_ids_str = ", ".join([f"'{fid}'" for fid in selected_file_ids])
            file_filter = f"\n5. IMPORTANT: You must ONLY search within nodes or entities related to the following file_ids: [{file_ids_str}]. If a node represents a Document or Chunk, it MUST have a file_id IN [{file_ids_str}]. If it is an entity, it MUST be connected to a Chunk/Document with a file_id IN [{file_ids_str}]."

        template = f"""
            You are a Neo4j expert. Given the following graph schema:
            {{schema}}

            Instructions:
            1. Focus on finding entities (like Person, Organization, etc.) that match the keywords in the question.
            2. If you find an entity, also look for its relationships to understand the context.
            3. For text matching, use:
                - CONTAINS for substring matching: WHERE c.text CONTAINS 'keyword'
                - toLower() for case-insensitive: WHERE toLower(c.text) CONTAINS 'keyword'
                - Regex for flexible matching: WHERE c.text =~ '(?i).*keyword.*'
                IMPORTANT: Do not use ILIKE as it is not valid Cypher syntax.
            4. If no specific entity is found, fall back to searching in 'Chunk' nodes.{file_filter}

            Question: {{question}}
            Cypher Query:
            """
        return PromptTemplate(
            input_variables=["schema", "question"],
            template=template,
        )

    def _create_chain(self, selected_file_ids: Optional[List[int]] = None):
        """Tạo GraphCypherQAChain"""
        if not self.neo4j_available or self.graph is None or GraphCypherQAChain is None:
            raise ValueError(
                "Neo4j graph not available. Cannot create GraphCypherQAChain."
            )
        cypher_prompt = self._get_cypher_prompt(selected_file_ids)
        chain = GraphCypherQAChain.from_llm(
            llm=self.llm,
            graph=self.graph,
            cypher_prompt=cypher_prompt,
            verbose=True,
            allow_dangerous_requests=True,
        )
        return chain

    def chat_flow(
        self,
        user_input: str,
        context_docs: Optional[List[Document]] = None,
        chat_history: Optional[List[Tuple[str, str]]] = None,
        selected_file_ids: Optional[List[int]] = None,
    ) -> str:
        """
        Luồng chat sử dụng Graph RAG.
        Nếu có context_docs (từ vector search), kết hợp graph và vector.
        Nếu không có context_docs, chỉ query graph.
        Nếu graph không khả dụng, fallback sang RAG thông thường.
        """
        # Nếu graph không khả dụng, fallback sang RAGService
        if not self.neo4j_available or self.graph is None:
            from src.services.rag.rag_service import RAGService

            rag = RAGService()
            return rag.chat_flow(
                user_input, context_docs=context_docs, chat_history=chat_history
            )

        # Xử lý lịch sử hội thoại (chỉ lấy 5 cặp gần nhất)
        history_text = ""
        if chat_history:
            for user_msg, assistant_msg in chat_history[-5:]:
                history_text += f"Người dùng: {user_msg}\nTrợ lý: {assistant_msg}\n"

        # Nếu có context_docs, thực hiện hybrid search
        if context_docs:
            return self.hybrid_search(user_input, context_docs, chat_history, selected_file_ids)

        # Chỉ query graph
        chain = self._create_chain(selected_file_ids)
        answer = chain.invoke({"query": user_input})
        result = answer.get("result", "")
        return result

    def query_graph(self, question: str, selected_file_ids: Optional[List[int]] = None) -> str:
        """Truy vấn đồ thị Neo4j trực tiếp"""
        if not self.neo4j_available or self.graph is None:
            raise ValueError("Neo4j graph not available.")
        chain = self._create_chain(selected_file_ids)
        answer = chain.invoke({"query": question})
        return answer.get("result", "")

    def hybrid_search(
        self,
        question: str,
        vector_docs: List[Document],
        chat_history: Optional[List[Tuple[str, str]]] = None,
        selected_file_ids: Optional[List[int]] = None,
    ) -> str:
        """
        Kết hợp graph query và vector search.
        Nếu graph trả về kết quả tốt, dùng graph; ngược lại dùng RAG thông thường.
        Nếu graph không khả dụng, fallback sang RAG thông thường.
        """
        if not self.neo4j_available or self.graph is None:
            from src.services.rag.rag_service import RAGService

            rag = RAGService()
            return rag.chat_flow(
                question, context_docs=vector_docs, chat_history=chat_history
            )

        graph_answer = self.query_graph(question, selected_file_ids)
        # Nếu graph answer không đủ, sử dụng vector docs với RAG
        if not graph_answer or "I don't know" in graph_answer.lower():
            from src.services.rag.rag_service import RAGService

            rag = RAGService()
            return rag.chat_flow(
                question, context_docs=vector_docs, chat_history=chat_history
            )
        return graph_answer

    # Các phương thức hỗ trợ self_rag (delegate tới RAGService)
    def rewrite_query(
        self, original_query: str, chat_history: List[Tuple[str, str]] = None
    ) -> str:
        from src.services.rag.rag_service import RAGService

        rag = RAGService()
        return rag.rewrite_query(original_query, chat_history)

    def evaluate_answer(self, question: str, answer: str, context: str) -> dict:
        from src.services.rag.rag_service import RAGService

        rag = RAGService()
        return rag.evaluate_answer(question, answer, context)

    def needs_more_info(self, question: str, answer: str, confidence: int) -> bool:
        from src.services.rag.rag_service import RAGService

        rag = RAGService()
        return rag.needs_more_info(question, answer, confidence)
