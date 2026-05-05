import os
from django.conf import settings
from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS

from src.models.chunk import Chunk
from src.core.rag.embedding_provider import get_embedding
from src.core.rag.cross_encoder import CrossEncoderReranker
from src.services.rag.file_ingestion_service import FileIngestionService
from src.services.rag.rag_service import RAGService
from src.services.rag.graph_rag_service import GraphRAGService
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
        vectorstore = self._load_vectorstore(conversation_id)
        if not vectorstore:
            return []

        if search_type == "hybrid":
            retriever = self._get_hybrid_retriever(
                conversation_id, top_k, selected_file_ids=selected_file_ids
            )
            if not retriever:
                return []
            docs = retriever.invoke(query)
            # Với hybrid, bm25 không có score, vector cũng không, nên có thể gán score = 0 hoặc None tùy ý
            # Nếu muốn score vector, bạn phải tự tính lại, nhưng tạm chấp nhận None
            if selected_file_ids:
                str_selected = [str(fid) for fid in selected_file_ids]
                docs = [
                    doc
                    for doc in docs
                    if str(doc.metadata.get("file_id")) in str_selected
                ]
            return docs[:top_k]
        else:
            # Vector search – LUÔN dùng similarity_search_with_score để lấy điểm
            if selected_file_ids:
                # Mỗi file lấy ít nhất 1 slot, chia đều top_k cho các file
                per_file_k = max(1, top_k // len(selected_file_ids))
                all_docs = []
                for fid in selected_file_ids:
                    docs_with_scores = vectorstore.similarity_search_with_score(
                        query, k=per_file_k, filter={"file_id": str(fid)}
                    )
                    for doc, score in docs_with_scores:
                        doc.metadata["score"] = float(score)
                        all_docs.append(doc)
                # Dedup, sắp xếp theo score (asc) rồi lấy top_k tổng
                seen = set()
                unique = []
                for doc in sorted(
                    all_docs, key=lambda d: d.metadata.get("score", float("inf"))
                ):
                    if doc.page_content not in seen:
                        seen.add(doc.page_content)
                        unique.append(doc)
                return unique[:top_k]
            else:
                docs_with_scores = vectorstore.similarity_search_with_score(
                    query, k=top_k
                )
                docs = []
                for doc, score in docs_with_scores:
                    doc.metadata["score"] = float(score)
                    docs.append(doc)
                return docs[:top_k]

    def _get_hybrid_retriever(
        self,
        conversation_id: int,
        top_k: int = 5,
        weights: tuple = (0.5, 0.5),
        selected_file_ids: list = None,
    ):
        vectorstore = self._load_vectorstore(conversation_id)
        if not vectorstore:
            return None
        vector_retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})

        chunk_qs = Chunk.objects.filter(conversation_id=conversation_id)
        if selected_file_ids:
            chunk_qs = chunk_qs.filter(file_id__in=selected_file_ids)
        if not chunk_qs:
            return vector_retriever

        from langchain_core.documents import Document

        documents = [
            Document(page_content=chunk.text, metadata=chunk.metadata)
            for chunk in chunk_qs
        ]
        bm25_retriever = BM25Retriever.from_documents(documents)
        bm25_retriever.k = top_k

        ensemble = EnsembleRetriever(
            retrievers=[vector_retriever, bm25_retriever], weights=weights
        )
        return ensemble

    def _build_response_item(self, resp_msg, content, citations, confidence, type_):
        return {
            "response_id": resp_msg.id,
            "type": type_,
            "content": content,
            "citations": citations,
            "word_count": len(content.split()),
            "created_at": resp_msg.created_at,
            "confidence": confidence,
        }

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

    def _create_conversation_and_check(self, user_id, conversation_id):
        conv = self.conv_repo.get_user_conversation_by_id(user_id, conversation_id)
        if not conv:
            raise ForbiddenException(
                "Cuộc hội thoại không tồn tại hoặc không có quyền truy cập"
            )
        return conv

    def _create_request_message(self, conv, question, selected_file_ids):
        req_msg = RequestMessage(conversation=conv, content=question)
        req_msg = self.req_repo.create(req_msg)
        if selected_file_ids:
            for fid in selected_file_ids:
                f = self.file_repo.get_one(id=fid, conversation_id=conv.id)
                if f:
                    self.selected_repo.create(
                        self.selected_repo.model_class(request_message=req_msg, file=f)
                    )
        return req_msg

    def _get_chat_history(self, conversation_id):
        """
        Trả về list tuple (user_msg, combined_assistant_msg) để dùng làm context.
        Nếu có nhiều response (dual mode), ghép lại với nhãn rõ ràng.
        """
        chat_history = []
        recent_requests = self.req_repo.get_recent(conversation_id, limit=5)
        for req in reversed(recent_requests):
            responses = self.resp_repo.get_by_request(req.id)  # tất cả response
            if not responses:
                continue

            # Gộp các response thành 1 chuỗi
            parts = []
            for r in responses:
                if r.type == "rag":
                    parts.append(f"[RAG] {r.content}")
                elif r.type == "graphrag":
                    parts.append(f"[GraphRAG] {r.content}")
                else:
                    parts.append(r.content)  # fallback
            combined_answer = "\n".join(parts)

            chat_history.append((req.content, combined_answer))
        return chat_history

    def _get_citations_for_response(self, response):
        citations = self.citation_repo.get_by_response(response.id)
        result = []
        for cit in citations:
            if cit.file:
                result.append(
                    {
                        "file_name": cit.file.file_name,
                        "file_url": build_url(cit.file.file_path),
                        "page": cit.page_number,
                        "chunk": cit.content_chunk,
                        "marker": cit.citation_marker,
                        "start_line": cit.start_line,
                        "end_line": cit.end_line,
                    }
                )
            else:
                result.append(
                    {
                        "marker": cit.citation_marker,
                        "graph_entity_name": cit.graph_entity_name,
                        "graph_entity_type": cit.graph_entity_type,
                    }
                )
        return result

    def _get_word_count_for_response(self, response):
        stat = self.stat_repo.get_by_response(response.id)  # gọi hàm mới
        return stat.word_count if stat else 0

    def get_history(self, conversation_id: int, user_id: int, cursor: str | None = None, limit: int=10):
        # Kiểm tra quyền truy cập conversation
        conv = self.conv_repo.get_user_conversation_by_id(user_id, conversation_id)
        if not conv:
            raise PermissionError("Không có quyền truy cập cuộc hội thoại")
        
        requests = self.req_repo.get_paginated(conversation_id, cursor=cursor, limit=limit+1)
        has_next = len(requests) > limit

        if has_next:
            requests = requests[:limit]

        next_cursor = None
        if requests:
            last = requests[-1]

            sort_time = last.created_at
            next_cursor = f"{sort_time.isoformat()}_{last.id}"

        history = []
        for req in requests:
            responses = list(self.resp_repo.get_by_request(req.id))
            types = {r.type for r in responses}
            is_dual = types == {"rag", "graphrag"}
            history.append({
                "request_id": req.id,
                "question": req.content,
                "created_at": req.created_at.isoformat() if req.created_at else None,
                "mode": "dual" if is_dual else "single",
                "responses": [
                    {
                        "response_id": r.id,
                        "type": r.type,  # "rag" hoặc "graphrag"
                        "content": r.content,
                        "citations": self._get_citations_for_response(r),
                        "word_count": self._get_word_count_for_response(r),
                        "created_at": r.created_at.isoformat() if r.created_at else None,
                    } for r in responses
                ]
            })
        return history, next_cursor, has_next

    def _retrieve_and_rerank(
        self,
        final_question,
        conversation_id,
        selected_file_ids,
        search_type,
        use_reranking,
        top_k,
        use_self_rag,
    ):
        retrieve_top_k = top_k * 2 if (use_reranking or use_self_rag) else top_k
        docs = self._retrieve_chunks_filtered(
            conversation_id,
            final_question,
            top_k=retrieve_top_k,
            selected_file_ids=selected_file_ids,
            search_type=search_type,
        )
        if use_reranking and docs:
            docs = self._rerank_docs(final_question, docs, top_k=top_k)
        elif use_self_rag and not use_reranking:
            docs = docs[:top_k]
        return docs

    def _build_rag_citations(self, docs, resp_msg=None):
        """Trả về list citations (dạng dict hoặc MessageCitation object nếu có resp_msg)."""
        citations = []
        if not docs:
            return citations
        counter = 1
        for doc in docs:
            file_id = doc.metadata.get("file_id")
            if file_id:
                file_obj = self.file_repo.get_one(id=file_id)
                
                if file_obj:
                    start_line, end_line = self._extract_citation_line_numbers(doc)
                    marker = self._format_citation_marker(counter, start_line, end_line)
                    if resp_msg:
                        cit = MessageCitation(
                            file=file_obj,
                            response_message=resp_msg,
                            page_number=doc.metadata.get("page", 0),
                            content_chunk=doc.page_content,
                            relevance_score=doc.metadata.get("score"),
                            start_line=start_line,
                            end_line=end_line,
                            citation_marker=marker,
                        )
                        self.citation_repo.create(cit)
                        citations.append(cit)
                    else:
                        citations.append(
                            {
                                "file_name": file_obj.file_name,                                
                                "file_path": file_obj.file_path,                                "file_url":  build_url(file_obj.file_path),
                                "page": doc.metadata.get("page", 0),
                                "chunk": doc.page_content,
                                "marker": marker,
                                "start_line": start_line,
                                "end_line": end_line,
                            }
                        )
                    counter += 1
        return citations

    def _build_graph_citations(self, citations_raw, resp_msg=None):
        """Trả về list citations graph (dạng dict hoặc MessageCitation object nếu có resp_msg)."""
        citations = []
        if not citations_raw:
            return citations
        for idx, cit_info in enumerate(citations_raw, 1):
            marker = f"【{idx}†G:{cit_info.get('id')}】"
            entity_name = cit_info.get("name", "")
            entity_id = cit_info.get("id")
            entity_type = cit_info.get("type")

            if resp_msg:
                cit = MessageCitation(
                    response_message=resp_msg,
                    file=None,  # Graph citations không gắn với file cụ thể
                    page_number=None,  # Không có page
                    content_chunk=None,  # Không có chunk text
                    citation_marker=marker,
                    graph_entity_id=entity_id,
                    graph_entity_name=entity_name,
                    graph_entity_type=entity_type,
                )
                self.citation_repo.create(cit)
                citations.append(cit)
            else:
                citations.append(
                    {
                        "graph_entity_id": entity_id,
                        "graph_entity_name": entity_name,
                        "graph_entity_type": entity_type,
                        "marker": marker,
                    }
                )
        return citations

    def _attach_citation_markers(self, docs: list) -> list:
        """Gắn citation_marker vào metadata từng doc để RAGService nhúng vào context."""
        for i, doc in enumerate(docs, 1):
            doc.metadata["citation_marker"] = f"【{i}】"
        return docs

    def _filter_cited_docs(self, answer: str, docs: list) -> list:
        """Chỉ giữ lại những doc có marker xuất hiện trong câu trả lời của LLM."""
        import re

        cited_markers = set(re.findall(r"【\d+】", answer))
        return [
            doc for doc in docs if doc.metadata.get("citation_marker") in cited_markers
        ]

    def _run_rag_pipeline(
        self,
        conversation_id,
        final_question,
        selected_file_ids,
        search_type,
        use_reranking,
        top_k,
        use_self_rag,
        chat_history,
    ):
        """
        Chạy RAG pipeline, trả về (answer, retrieved_docs, confidence).
        Không lưu citations ở đây — việc lưu DB được tách ra ngoài.
        """
        svc = RAGService()
        retrieved_docs = self._retrieve_and_rerank(
            final_question,
            conversation_id,
            selected_file_ids,
            search_type,
            use_reranking,
            top_k,
            use_self_rag,
        )

        answer = svc.chat_flow(
            final_question, context_docs=retrieved_docs, chat_history=chat_history
        )

        confidence = None
        if use_self_rag:
            context_text = (
                "\n".join([doc.page_content for doc in retrieved_docs])
                if retrieved_docs
                else ""
            )
            evaluation = svc.evaluate_answer(final_question, answer, context_text)
            confidence = evaluation.get("confidence")

            # Multi-hop nếu confidence thấp
            if confidence is not None and confidence < 60:
                extra_docs = self._retrieve_chunks_filtered(
                    conversation_id,
                    f"Cung cấp thêm: {final_question}",
                    top_k=top_k,
                    selected_file_ids=selected_file_ids,
                    search_type=search_type,
                )
                if extra_docs:
                    merged = {d.page_content: d for d in retrieved_docs + extra_docs}
                    retrieved_docs = list(merged.values())[: top_k * 2]
                    answer = svc.chat_flow(
                        final_question,
                        context_docs=retrieved_docs,
                        chat_history=chat_history,
                    )

        return answer, retrieved_docs, confidence

    def _run_graph_pipeline(
        self,
        conversation_id,
        final_question,
        selected_file_ids,
        use_self_rag,
        chat_history,
    ):
        """
        Chạy Graph RAG pipeline, trả về (answer, citations_raw, confidence).
        Không lưu citations ở đây — việc lưu DB được tách ra ngoài.
        """
        svc = GraphRAGService()
        result = svc.chat_flow(
            final_question,
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

        # Tính confidence nếu cần (dùng RAGService vì GraphRAG không có context text)
        confidence = None
        if use_self_rag:
            temp_rag = RAGService()
            evaluation = temp_rag.evaluate_answer(final_question, answer, "")
            confidence = evaluation.get("confidence")

        return answer, citations_raw, confidence

    def ask(
        self,
        conversation_id,
        user_id,
        question,
        selected_file_ids=None,
        response_type="rag",
        search_type="vector",
        use_reranking=False,
        top_k=5,
        use_self_rag=False,
    ):

        # 1. Kiểm tra conversation và tạo request message
        conv = self._create_conversation_and_check(user_id, conversation_id)
        req_msg = self._create_request_message(conv, question, selected_file_ids)
        chat_history = self._get_chat_history(conversation_id)

        # 2. Rewrite query nếu dùng self-rag
        final_question = question
        if use_self_rag and chat_history:
            temp_svc = RAGService()
            final_question = temp_svc.rewrite_query(question, chat_history)

        # 3. Dual mode
        if response_type == "dual":
            # 1. Run pipelines
            rag_answer, rag_docs, rag_conf = self._run_rag_pipeline(
                conversation_id,
                final_question,
                selected_file_ids,
                search_type,
                use_reranking,
                top_k,
                use_self_rag,
                chat_history,
            )

            graph_answer, graph_citations_raw, graph_conf = self._run_graph_pipeline(
                conversation_id,
                final_question,
                selected_file_ids,
                use_self_rag,
                chat_history,
            )

            # 2. Create RAG response
            rag_resp = ResponseMessage(
                request_message=req_msg, content=rag_answer, type="rag"
            )
            rag_resp = self.resp_repo.create(rag_resp)

            rag_citation_objs = self._build_rag_citations(rag_docs, resp_msg=rag_resp)

            self.stat_repo.create(MessageStat(
                message=rag_resp,
                word_count=len(rag_answer.split())
            ))

            # 3. Create GraphRAG response
            graph_resp = ResponseMessage(
                request_message=req_msg, content=graph_answer, type="graphrag"
            )
            graph_resp = self.resp_repo.create(graph_resp)

            graph_citation_objs = self._build_graph_citations(
                graph_citations_raw,
                resp_msg=graph_resp
            )

            self.stat_repo.create(MessageStat(
                message=graph_resp,
                word_count=len(graph_answer.split())
            ))

            # 4. Build unified response items
            rag_item = self._build_response_item(
                rag_resp,
                rag_answer,
                [
                    {
                        "file_name": c.file.file_name if c.file else "Unknown",
                        "file_path": build_url(c.file.file_path) if c.file else None,
                        "page": c.page_number,
                        "chunk": c.content_chunk,
                        "marker": c.citation_marker,
                        "start_line": c.start_line,
                        "end_line": c.end_line,
                    } for c in rag_citation_objs
                ],
                rag_conf,
                "rag"
            )

            graph_item = self._build_response_item(
                graph_resp,
                graph_answer,
                [
                    {
                        "marker": c.citation_marker,
                        "graph_entity_name": c.graph_entity_name,
                        "graph_entity_type": c.graph_entity_type,
                    } for c in graph_citation_objs
                ],
                graph_conf,
                "graphrag"
            )

            # 5. Final unified response
            return {
                "request_id": req_msg.id,
                "question": req_msg.content,
                "created_at": req_msg.created_at,
                "mode": "dual",
                "responses": [rag_item, graph_item],
                "rewritten_query": final_question if use_self_rag else None,
            }

        # 4. Single mode RAG
        if response_type == "rag":
            answer, retrieved_docs, confidence = self._run_rag_pipeline(
                conversation_id,
                final_question,
                selected_file_ids,
                search_type,
                use_reranking,
                top_k,
                use_self_rag,
                chat_history,
            )

            resp_msg = ResponseMessage(
                request_message=req_msg,
                content=answer,
                type="rag"
            )
            resp_msg = self.resp_repo.create(resp_msg)

            citations_objs = self._build_rag_citations(retrieved_docs, resp_msg=resp_msg)

            self.stat_repo.create(MessageStat(
                message=resp_msg,
                word_count=len(answer.split())
            ))

            response_item = self._build_response_item(
                resp_msg,
                answer,
                [
                    {
                        "file_name": c.file.file_name if c.file else "Unknown",
                        "file_path": build_url(c.file.file_path) if c.file else None,
                        "page": c.page_number,
                        "chunk": c.content_chunk,
                        "marker": c.citation_marker,
                        "start_line": c.start_line,
                        "end_line": c.end_line,
                    }
                    for c in citations_objs
                ],
                confidence,
                "rag"
            )

            return {
                "request_id": req_msg.id,
                "question": req_msg.content,
                "created_at": req_msg.created_at,
                "mode": "single",
                "responses": [response_item],
                "rewritten_query": final_question if use_self_rag else None,
            }

        # 5. Single mode GraphRAG
        if response_type == "graph_rag":
            answer, citations_raw, confidence = self._run_graph_pipeline(
                conversation_id,
                final_question,
                selected_file_ids,
                use_self_rag,
                chat_history,
            )

            resp_msg = ResponseMessage(
                request_message=req_msg,
                content=answer,
                type="graph_rag"
            )
            resp_msg = self.resp_repo.create(resp_msg)

            citations_objs = self._build_graph_citations(citations_raw, resp_msg=resp_msg)

            self.stat_repo.create(MessageStat(
                message=resp_msg,
                word_count=len(answer.split())
            ))

            response_item = self._build_response_item(
                resp_msg,
                answer,
                [
                    {
                        "marker": c.citation_marker,
                        "graph_entity_name": c.graph_entity_name,
                        "graph_entity_type": c.graph_entity_type,
                    } for c in citations_objs
                ],
                confidence,
                "graphrag"
            )

            return {
                "request_id": req_msg.id,
                "question": req_msg.content,
                "created_at": req_msg.created_at,
                "mode": "single",
                "responses": [response_item],
                "rewritten_query": final_question if use_self_rag else None,
            }

    def clear_history(self, conversation_id: int, user_id: int):
        # Kiểm tra quyền truy cập (sẽ raise ForbiddenException nếu ko hợp lệ)
        self._create_conversation_and_check(user_id, conversation_id)
        # Thực hiện xóa tất cả request (cascade)
        self.req_repo.delete_by_conversation(conversation_id)
        

def build_url(file_path):
        file = os.path.basename(file_path)
        print(file)
        return f"http://127.0.0.1:8000/media/files/{file}"
