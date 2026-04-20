import os
from typing import List, Optional
from django.conf import settings
from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS

from src.models.chunk import Chunk
from src.core.rag.embedding_provider import get_embedding
from src.core.rag.cross_encoder import CrossEncoderReranker
from src.services.rag.file_ingestion_service import FileIngestionService
from src.services.rag.rag_service import RAGService
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.request_message_repository import RequestMessageRepository
from src.repositories.response_message_repository import ResponseMessageRepository
from src.repositories.file_repository import FileRepository
from src.repositories.request_selected_file_repository import (
    RequestSelectedFileRepository,
)
from src.repositories.message_citation_repository import MessageCitationRepository
from src.repositories.message_stat_repository import MessageStatRepository
from src.models.request_messages import RequestMessage
from src.models.response_messages import ResponseMessage
from src.models.message_citations import MessageCitation
from src.models.message_stats import MessageStat
from src.core.exceptions import ForbiddenException

VECTOR_DB_ROOT = os.path.join(settings.BASE_DIR, "vector_db")


class ChatService:
    def __init__(
        self,
        conv_repo: ConversationRepository,
        req_repo: RequestMessageRepository,
        resp_repo: ResponseMessageRepository,
        file_repo: FileRepository,
        selected_repo: RequestSelectedFileRepository,
        citation_repo: MessageCitationRepository,
        stat_repo: MessageStatRepository,
        ingestion_service: FileIngestionService,
        reranker: CrossEncoderReranker,
    ):
        self.conv_repo = conv_repo
        self.req_repo = req_repo
        self.resp_repo = resp_repo
        self.file_repo = file_repo
        self.selected_repo = selected_repo
        self.citation_repo = citation_repo
        self.stat_repo = stat_repo
        self.ingestion_service = ingestion_service
        self.embedding = get_embedding()
        self.reranker = reranker

    def _get_vector_store_path(self, conversation_id: int) -> str:
        return os.path.join(VECTOR_DB_ROOT, f"conv_{conversation_id}")

    def _load_vectorstore(self, conversation_id: int):
        path = self._get_vector_store_path(conversation_id)
        if os.path.exists(path):
            return FAISS.load_local(
                path, self.embedding, allow_dangerous_deserialization=True
            )
        return None

    def _rerank_docs(self, query: str, docs: list, top_k: int = 5) -> list:
        """Re-rank documents using cross-encoder."""
        if not docs:
            return docs
        return self.reranker.rerank(query, docs, top_k=top_k)

    def _retrieve_chunks_filtered(
        self,
        conversation_id,
        query,
        top_k=5,
        selected_file_ids=None,
        search_type="vector",
    ):
        if search_type == "hybrid":
            retriever = self._get_hybrid_retriever(conversation_id, top_k)
            if not retriever:
                return []
            docs = retriever.invoke(query)
            if selected_file_ids:
                str_selected = [str(fid) for fid in selected_file_ids]
                docs = [
                    doc
                    for doc in docs
                    if str(doc.metadata.get("file_id")) in str_selected
                ]
            return docs[:top_k]
        else:
            # vector search (giữ nguyên)
            vectorstore = self._load_vectorstore(conversation_id)
            if not vectorstore:
                return []
            if selected_file_ids:
                all_docs = []
                for fid in selected_file_ids:
                    docs = vectorstore.similarity_search(
                        query, k=top_k, filter={"file_id": str(fid)}
                    )
                    all_docs.extend(docs)
                seen = set()
                unique = []
                for doc in all_docs:
                    key = doc.page_content
                    if key not in seen:
                        seen.add(key)
                        unique.append(doc)
                return unique[:top_k]
            else:
                retriever = self.ingestion_service.get_retriever(
                    vectorstore, top_k=top_k
                )
                return retriever.invoke(query)

    def ask(
        self,
        conversation_id: int,
        user_id: int,
        question: str,
        selected_file_ids: Optional[List[int]] = None,
        response_type: str = "rag",
        search_type: str = "vector",
        use_reranking: bool = False,
        top_k: int = 5,
        use_self_rag: bool = False,
    ):

        # Kiểm tra quyền
        conv = self.conv_repo.get_user_conversation_by_id(user_id, conversation_id)
        if not conv:
            raise ForbiddenException(
                "Cuộc hội thoại không tồn tại hoặc không có quyền truy cập"
            )

        # Tạo request message
        req_msg = RequestMessage(conversation=conv, content=question)
        req_msg = self.req_repo.create(req_msg)

        # Lưu selected files nếu có
        if selected_file_ids:
            for fid in selected_file_ids:
                f = self.file_repo.get_one(id=fid, conversation_id=conversation_id)
                if f:
                    self.selected_repo.create(
                        self.selected_repo.model_class(request_message=req_msg, file=f)
                    )

        # Lấy lịch sử hội thoại
        chat_history = []
        # Lấy 5 request mới nhất (từ repository)
        recent_requests = self.req_repo.get_recent(conversation_id, limit=5)
        # Đảo ngược để có thứ tự từ cũ đến mới (đúng trình tự hội thoại)
        for req in reversed(recent_requests):
            resp = self.resp_repo.get_one(request_message_id=req.id)
            if resp:
                chat_history.append((req.content, resp.content))

        # Retrieve
        retrieved_docs = []
        if response_type == "rag":
            retrieved_docs = self._retrieve_chunks_filtered(
                conversation_id,
                question,
                top_k=top_k * 2 if use_reranking else top_k,
                selected_file_ids=selected_file_ids,
                search_type=search_type,
            )
            if use_reranking and retrieved_docs:
                retrieved_docs = self._rerank_docs(
                    question, retrieved_docs, top_k=top_k
                )

        rag = RAGService()

        final_question = question
        if use_self_rag and chat_history:
            final_question = rag.rewrite_query(question, chat_history)

            # Retrieve (chỉ một lần)
        retrieve_top_k = top_k * 2 if (use_reranking or use_self_rag) else top_k
        retrieved_docs = self._retrieve_chunks_filtered(
            conversation_id,
            final_question,
            top_k=retrieve_top_k,
            selected_file_ids=selected_file_ids,
            search_type=search_type,
        )
        if use_reranking and retrieved_docs:
            retrieved_docs = self._rerank_docs(
                final_question, retrieved_docs, top_k=top_k
            )
        elif use_self_rag and not use_reranking:
            retrieved_docs = retrieved_docs[:top_k]

        answer = rag.chat_flow(
            final_question, context_docs=retrieved_docs, chat_history=chat_history
        )

        # Self-evaluation
        confidence = None
        if use_self_rag:
            context_text = "\n".join([doc.page_content for doc in retrieved_docs])
            evaluation = rag.evaluate_answer(final_question, answer, context_text)
            confidence = evaluation.get("confidence")
            if rag.needs_more_info(final_question, answer, confidence):
                extra_docs = self._retrieve_chunks_filtered(
                    conversation_id,
                    f"Cung cấp thêm: {final_question}",
                    top_k=top_k,
                    selected_file_ids=selected_file_ids,
                    search_type=search_type,
                )
                if extra_docs:
                    all_docs = retrieved_docs + extra_docs
                    seen = set()
                    unique_docs = []
                    for doc in all_docs:
                        key = doc.page_content
                        if key not in seen:
                            seen.add(key)
                            unique_docs.append(doc)
                    answer = rag.chat_flow(
                        final_question,
                        context_docs=unique_docs[: top_k * 2],
                        chat_history=chat_history,
                    )

        # Tạo response
        resp_msg = ResponseMessage(
            request_message=req_msg, content=answer, type=response_type
        )
        resp_msg = self.resp_repo.create(resp_msg)

        # Tạo citations
        citations = []
        citation_counter = 1
        for doc in retrieved_docs:
            file_id = doc.metadata.get("file_id")
            if file_id:
                file_obj = self.file_repo.get_one(id=file_id)
                if file_obj:
                    start_line, end_line = self._extract_citation_line_numbers(doc)
                    citation_marker = self._format_citation_marker(
                        citation_counter, start_line, end_line
                    )

                    cit = MessageCitation(
                        file=file_obj,
                        response_message=resp_msg,
                        page_number=doc.metadata.get("page", 0),
                        content_chunk=doc.page_content,
                        relevance_score=doc.metadata.get("score"),
                        start_line=start_line,
                        end_line=end_line,
                        citation_marker=citation_marker,
                    )
                    self.citation_repo.create(cit)
                    citations.append(cit)
                    citation_counter += 1
        # Tạo stat
        self.stat_repo.create(
            MessageStat(message=resp_msg, word_count=len(answer.split()))
        )

        return {
            "request_id": req_msg.id,
            "response_id": resp_msg.id,
            "answer": answer,
            "citations": [
                {
                    "file_name": c.file.file_name,
                    "page": c.page_number,
                    "chunk": c.content_chunk,
                    "marker": c.citation_marker,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                }
                for c in citations
            ],
            "confidence": confidence,
            "rewritten_query": final_question if use_self_rag else None,
        }

    def get_history(self, conversation_id: int, user_id: int, skip=0, limit=50):
        conv = self.conv_repo.get_user_conversation_by_id(user_id, conversation_id)
        if not conv:
            raise ForbiddenException(
                "Cuộc hội thoại không tồn tại hoặc không có quyền truy cập"
            )
        requests, total = self.req_repo.get_by_conversation_id(
            conversation_id, skip, limit
        )
        history = []
        for req in requests:
            resp = self.resp_repo.get_one(request_message_id=req.id)
            history.append(
                {
                    "request_id": req.id,
                    "question": req.content,
                    "answer": resp.content if resp else "",
                    "created_at": req.created_at,
                }
            )
        return history, total

    def clear_history(self, conversation_id: int, user_id: int):
        conv = self.conv_repo.get_user_conversation_by_id(user_id, conversation_id)
        if not conv:
            raise ForbiddenException(
                "Cuộc hội thoại không tồn tại hoặc không có quyền truy cập"
            )
        requests, _ = self.req_repo.get_all(
            conversation_id=conversation_id, limit=10000
        )
        for req in requests:
            # Xóa response message (cascade sẽ xóa citations, stats)
            self.resp_repo.delete_by_request_message_id(req.id)
            self.req_repo.delete(req)
        return True

    def _get_hybrid_retriever(
        self, conversation_id: int, top_k: int = 5, weights: tuple = (0.5, 0.5)
    ):
        vectorstore = self._load_vectorstore(conversation_id)
        if not vectorstore:
            return None
        vector_retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})

        # Lấy các chunk object có metadata
        chunks = Chunk.objects.filter(conversation_id=conversation_id)
        if not chunks:
            return vector_retriever
        # Tạo list Document với metadata
        from langchain_core.documents import Document

        documents = []
        for chunk in chunks:
            doc = Document(page_content=chunk.text, metadata=chunk.metadata)
            documents.append(doc)
        bm25_retriever = BM25Retriever.from_documents(documents)
        bm25_retriever.k = top_k

        ensemble = EnsembleRetriever(
            retrievers=[vector_retriever, bm25_retriever], weights=weights
        )
        return ensemble

    def _get_line_numbers(self, content: str, char_index: int) -> int:
        """Tính số dòng (1-indexed) từ vị trí ký tự trong nội dung."""
        if char_index is None or char_index < 0:
            return 0
        return content[:char_index].count("\n") + 1

    def _extract_citation_line_numbers(self, doc) -> tuple[int, int]:
        """Trích xuất start_line và end_line từ metadata của Document."""
        content = doc.page_content
        start_idx = doc.metadata.get("start_index", 0)
        end_idx = start_idx + len(content)
        start_line = self._get_line_numbers(content, start_idx)
        # Đối với end_line, lấy vị trí ký tự cuối cùng của chunk (end_idx-1)
        end_line = self._get_line_numbers(content, max(end_idx - 1, 0))
        return start_line, end_line

    def _format_citation_marker(
        self, citation_id: int, start_line: int, end_line: int
    ) -> str:
        """Tạo citation marker theo định dạng 【id†Lstart[-Lend]】."""
        if start_line == end_line or end_line == 0:
            return f"【{citation_id}†L{start_line}】"
        else:
            return f"【{citation_id}†L{start_line}-L{end_line}】"
