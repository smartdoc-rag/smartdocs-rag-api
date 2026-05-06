from typing import List, Optional, Tuple, Callable
from langchain_core.documents import Document
from src.services.rag.rag_service import RAGService


class RagPipeline:
    """
    Xử lý sinh câu trả lời từ truy vấn + các văn bản đã retrieve.
    Có thể tích hợp Self-RAG (đánh giá, multi-hop nếu cần).
    """

    def __init__(self, rag_service: RAGService = None):
        self.rag_service = rag_service or RAGService()

    def run(
        self,
        query: str,
        context_docs: List[Document],
        chat_history: list,
        use_self_rag: bool = False,
        top_k: int = 5,
        extra_retriever: Optional[Callable[[str], List[Document]]] = None,
    ) -> Tuple[str, List[Document], Optional[float]]:
        """
        Sinh câu trả lời RAG.

        Args:
            query: câu hỏi gốc (đã được rewrite nếu dùng Self-RAG)
            context_docs: danh sách Document đã retrieve và rerank
            chat_history: lịch sử chat dạng [(user, bot), ...]
            use_self_rag: bật Self-RAG (đánh giá độ tin cậy)
            top_k: số lượng chunk dùng để regenerate khi confidence thấp
            extra_retriever: hàm nhận query mới, trả về thêm Document (cho multi-hop)

        Returns:
            (answer, final_docs, confidence)
        """
        answer = self.rag_service.chat_flow(
            query, context_docs=context_docs, chat_history=chat_history
        )
        final_docs = context_docs
        confidence = None

        if use_self_rag:
            context_text = (
                "\n".join([doc.page_content for doc in context_docs])
                if context_docs
                else ""
            )
            evaluation = self.rag_service.evaluate_answer(query, answer, context_text)
            confidence = evaluation.get("confidence")

            # Multi-hop nếu confidence thấp và có callback extra_retriever
            if (
                confidence is not None
                and confidence < 60
                and extra_retriever
            ):
                extra_docs = extra_retriever(
                    f"Cung cấp thêm: {query}"
                )
                if extra_docs:
                    # merge & deduplicate, giữ limit top_k * 2
                    merged = {
                        d.page_content: d
                        for d in context_docs + extra_docs
                    }
                    final_docs = list(merged.values())[: top_k * 2]
                    answer = self.rag_service.chat_flow(
                        query,
                        context_docs=final_docs,
                        chat_history=chat_history,
                    )

        return answer, final_docs, confidence