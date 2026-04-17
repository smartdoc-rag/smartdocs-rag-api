import os
from typing import List, Optional, Tuple
from django.conf import settings
from langchain_community.vectorstores import FAISS
from src.core.rag.embedding_provider import get_embedding
from src.services.rag.file_ingestion_service import FileIngestionService
from src.services.rag.rag_service import RAGService
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.request_message_repository import RequestMessageRepository
from src.repositories.response_message_repository import ResponseMessageRepository
from src.repositories.file_repository import FileRepository
from src.repositories.request_selected_file_repository import RequestSelectedFileRepository
from src.repositories.message_citation_repository import MessageCitationRepository
from src.repositories.message_stat_repository import MessageStatRepository
from src.models.request_messages import RequestMessage
from src.models.response_messages import ResponseMessage
from src.models.message_citations import MessageCitation
from src.models.message_stats import MessageStat

VECTOR_DB_ROOT = os.path.join(settings.BASE_DIR, "vector_db")

class ChatService:
    def __init__(self):
        self.conv_repo = ConversationRepository()
        self.req_repo = RequestMessageRepository()
        self.resp_repo = ResponseMessageRepository()
        self.file_repo = FileRepository()
        self.selected_repo = RequestSelectedFileRepository()
        self.citation_repo = MessageCitationRepository()
        self.stat_repo = MessageStatRepository()
        self.ingestion_service = FileIngestionService()
        self.embedding = get_embedding()

    def _get_vector_store_path(self, conversation_id: int) -> str:
        return os.path.join(VECTOR_DB_ROOT, f"conv_{conversation_id}")

    def _load_vectorstore(self, conversation_id: int):
        path = self._get_vector_store_path(conversation_id)
        if os.path.exists(path):
            return FAISS.load_local(path, self.embedding, allow_dangerous_deserialization=True)
        return None

    def _retrieve_chunks(self, conversation_id: int, query: str, top_k=5):
        vectorstore = self._load_vectorstore(conversation_id)
        if not vectorstore:
            return []
        retriever = self.ingestion_service.get_retriever(vectorstore, top_k=top_k)
        return retriever.invoke(query)

    def ask(self, conversation_id: int, user_id: int, question: str,
            selected_file_ids: Optional[List[int]] = None, response_type: str = "rag"):
        # Kiểm tra quyền
        conv = self.conv_repo.get_user_conversation_by_id(user_id, conversation_id)
        if not conv:
            raise PermissionError("Conversation not found or access denied")

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

        # Retrieve
        retrieved_docs = []
        if response_type == "rag":
            retrieved_docs = self._retrieve_chunks(conversation_id, question, top_k=5)

        # Gọi RAGService (đã sửa để nhận context_docs)
        rag = RAGService()
        answer = rag.chat_flow(question, context_docs=retrieved_docs)

        # Tạo response
        resp_msg = ResponseMessage(request_message=req_msg, content=answer, type=response_type)
        resp_msg = self.resp_repo.create(resp_msg)

        # Tạo citations
        citations = []
        for doc in retrieved_docs:
            file_id = doc.metadata.get('file_id')
            if file_id:
                file_obj = self.file_repo.get_one(id=file_id)
                if file_obj:
                    cit = MessageCitation(
                        file=file_obj,
                        response_message=resp_msg,
                        page_number=doc.metadata.get('page', 0),
                        content_chunk=doc.page_content,
                        relevance_score=doc.metadata.get('score')
                    )
                    self.citation_repo.create(cit)
                    citations.append(cit)

        # Tạo stat
        self.stat_repo.create(MessageStat(message=resp_msg, word_count=len(answer.split())))

        return {
            "request_id": req_msg.id,
            "response_id": resp_msg.id,
            "answer": answer,
            "citations": [{"file_name": c.file.file_name, "page": c.page_number, "chunk": c.content_chunk} for c in citations]
        }

    def get_history(self, conversation_id: int, user_id: int, skip=0, limit=50):
        conv = self.conv_repo.get_user_conversation_by_id(user_id, conversation_id)
        if not conv:
            raise PermissionError()
        requests, total = self.req_repo.get_by_conversation_id(conversation_id, skip, limit)
        history = []
        for req in requests:
            resp = self.resp_repo.get_one(request_message_id=req.id)
            history.append({
                "request_id": req.id,
                "question": req.content,
                "answer": resp.content if resp else "",
                "created_at": req.created_at
            })
        return history, total

    def clear_history(self, conversation_id: int, user_id: int):
        conv = self.conv_repo.get_user_conversation_by_id(user_id, conversation_id)
        if not conv:
            raise PermissionError()
        requests, _ = self.req_repo.get_all(conversation_id=conversation_id, limit=10000)
        for req in requests:
            # Xóa response message (cascade sẽ xóa citations, stats)
            self.resp_repo.delete_by_request_message_id(req.id)
            self.req_repo.delete(req)
        return True