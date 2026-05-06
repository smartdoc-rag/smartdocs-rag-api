from typing import List, Optional, Tuple, Dict, Any
from src.services.rag.graph_rag_service import GraphRAGService
from src.services.rag.rag_service import RAGService


class GraphRagPipeline:
    """
    Pipeline cho Knowledge Graph RAG.
    Tự thực hiện truy vấn đồ thị và sinh câu trả lời.
    """

    def __init__(self, graph_rag_service: GraphRAGService = None):
        self.graph_rag_service = graph_rag_service or GraphRAGService()

    def run(
        self,
        query: str,
        conversation_id: int,
        selected_file_ids: list,
        chat_history: list,
        use_self_rag: bool = False,
    ) -> Tuple[str, List[Dict[str, Any]], Optional[float]]:
        """
        Returns:
            (answer, citations_raw, confidence)
            citations_raw: danh sách dict chứa thông tin entity graph.
        """
        result = self.graph_rag_service.chat_flow(
            query,
            context_docs=None,
            chat_history=chat_history,
            selected_file_ids=selected_file_ids,
            conversation_id=conversation_id,
        )

        if isinstance(result, dict):
            answer = result.get("answer", "")
            citations_raw = result.get("citations", [])
        else:
            answer = result
            citations_raw = []

        confidence = None
        if use_self_rag:
            # Graph không có context text -> dùng RAGService tạm để evaluate
            temp_rag = RAGService()
            evaluation = temp_rag.evaluate_answer(query, answer, "")
            confidence = evaluation.get("confidence")

        return answer, citations_raw, confidence