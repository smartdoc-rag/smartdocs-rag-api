# Phân tích hiện trạng SmartDoc RAG API (Django backend cho React)

_Cập nhật: 2026-04-18 (re-check theo code hiện tại)_

## 1) Phạm vi kiểm tra

- Nguồn đối chiếu yêu cầu: yêu cầu assignment phần RAG backend (Q1 -> Q10).
- Nguồn đối chiếu hiện trạng: toàn bộ mã trong workspace, không đọc thư mục .venv.
- Bối cảnh triển khai: frontend dùng React, nên backend cần hoàn chỉnh ở dạng REST API có thể gọi độc lập.

## 2) Thang trọng số đánh giá

- Trọng số tổng: 100.
- Có thêm hạng mục A0 (API readiness) vì đây là điều kiện bắt buộc khi FE là React.
- Cách tính điểm đạt: Trọng số x Mức hoàn thành.

| Mã | Hạng mục | Trọng số | Trạng thái | Mức hoàn thành | Điểm đạt | Minh chứng chính |
|---|---|---:|---|---:|---:|---|
| A0 | Đóng gói backend thành API hoàn chỉnh cho React (auth/user/file/chat/history/conversation) | 25 | Làm một phần (tiến triển mạnh) | 80% | 20.0 | Đã expose route auth/user/chat/file/conversation tại [src/urls.py](src/urls.py), cùng endpoint trong [src/api/chat/views.py](src/api/chat/views.py), [src/api/file/views.py](src/api/file/views.py), [src/api/conversation/views.py](src/api/conversation/views.py) |
| Q1 | Hỗ trợ file DOCX | 6 | Làm một phần (khá tốt) | 80% | 4.8 | Upload DOCX + loader Docx2txt có trong [src/services/file_service.py](src/services/file_service.py), type DOCX có trong [src/models/files.py](src/models/files.py) |
| Q2 | Lưu lịch sử hội thoại | 8 | Làm một phần (khá tốt) | 80% | 6.4 | Có lưu request/response message và API history tại [src/services/chat_service.py](src/services/chat_service.py), [src/api/chat/views.py](src/api/chat/views.py), [src/models/request_messages.py](src/models/request_messages.py), [src/models/response_messages.py](src/models/response_messages.py) |
| Q3 | Clear History + Clear Vector Store | 5 | Làm một phần (khá tốt) | 80% | 4.0 | Có clear history ở [src/api/chat/views.py](src/api/chat/views.py), [src/services/chat_service.py](src/services/chat_service.py) và clear vector store khi clear file ở [src/api/file/views.py](src/api/file/views.py), [src/services/file_service.py](src/services/file_service.py) |
| Q4 | Cải thiện chunk strategy | 7 | Làm một phần | 35% | 2.5 | Có splitter với separator tốt hơn tại [src/services/rag/file_ingestion_service.py](src/services/rag/file_ingestion_service.py), nhưng chunk size/overlap vẫn hard-code |
| Q5 | Citation/source tracking | 8 | Làm một phần (khá tốt) | 70% | 5.6 | Có model/repo citation và đã ghi citation sau truy hồi tại [src/models/message_citations.py](src/models/message_citations.py), [src/repositories/message_citation_repository.py](src/repositories/message_citation_repository.py), [src/services/chat_service.py](src/services/chat_service.py) |
| Q6 | Conversational RAG | 10 | Làm một phần | 30% | 3.0 | Prompt có biến history tại [src/core/rag/prompt.py](src/core/rag/prompt.py), nhưng hiện vẫn truyền history rỗng ở [src/services/rag/rag_service.py](src/services/rag/rag_service.py) |
| Q7 | Hybrid search (semantic + BM25) | 8 | Chưa làm | 0% | 0.0 | Retriever hiện chỉ similarity trong [src/services/rag/file_ingestion_service.py](src/services/rag/file_ingestion_service.py), chưa có BM25/ensemble |
| Q8 | Multi-document + metadata filtering | 10 | Làm một phần | 40% | 4.0 | Có upload nhiều file theo conversation + selected_file_ids được lưu ở [src/services/chat_service.py](src/services/chat_service.py), [src/models/request_selected_files.py](src/models/request_selected_files.py), nhưng retrieval chưa filter theo selected file/metadata |
| Q9 | Re-ranking với Cross-Encoder | 7 | Chưa làm | 0% | 0.0 | Chưa có lớp reranker/cross-encoder trong src |
| Q10 | Self-RAG (query rewrite, confidence, multi-hop) | 6 | Chưa làm | 0% | 0.0 | Chưa có flow tự đánh giá/chỉnh truy vấn/scoring |

**Tổng điểm hiện tại (ước tính): 50.3 / 100**

## 3) Tiến độ hiện tại

### Đã hoàn thành hoặc đã có luồng chạy được

- Đã API hóa backend cho React ở các luồng chính: auth, user, chat, file, conversation ([src/urls.py](src/urls.py)).
- Đã có migration schema thực tế: [src/migrations/0001_initial.py](src/migrations/0001_initial.py).
- Đã có upload và ingest PDF/DOCX vào FAISS theo conversation: [src/services/file_service.py](src/services/file_service.py).
- Đã có lưu lịch sử chat request/response + trả về history endpoint: [src/services/chat_service.py](src/services/chat_service.py), [src/api/chat/views.py](src/api/chat/views.py).
- Đã có clear-history và clear-files (kèm xóa vector store theo conversation): [src/api/chat/views.py](src/api/chat/views.py), [src/api/file/views.py](src/api/file/views.py), [src/services/file_service.py](src/services/file_service.py).
- Đã có lưu citation theo response message và trả citation trong response chat: [src/services/chat_service.py](src/services/chat_service.py).

### Chưa hoàn thiện

- Chưa đưa lịch sử hội thoại thực tế vào prompt RAG (history đang rỗng): [src/services/rag/rag_service.py](src/services/rag/rag_service.py).
- Chưa filter retrieval theo selected file/metadata dù đã lưu selected_file_ids: [src/services/chat_service.py](src/services/chat_service.py).
- Chưa có hybrid search (BM25 + semantic), rerank cross-encoder, self-RAG.
- Chưa có test tự động cho các luồng chính (không tìm thấy test file trong workspace).

## 4) Blocker và rủi ro kỹ thuật

### Blocker cũ đã đóng

- Đã thống nhất field mật khẩu `password_hash` giữa model và auth service: [src/models/user.py](src/models/user.py), [src/services/auth_service.py](src/services/auth_service.py).
- Đã có cột `role` trong user model và migration: [src/models/user.py](src/models/user.py), [src/migrations/0001_initial.py](src/migrations/0001_initial.py).
- API user hiện gọi đúng service method `get_all`: [src/api/user/views.py](src/api/user/views.py), [src/services/user_service.py](src/services/user_service.py).
- Delete user đã truyền object model vào repository delete: [src/services/user_service.py](src/services/user_service.py), [src/repositories/base.py](src/repositories/base.py).

### Rủi ro còn mở (ưu tiên sửa tiếp)

- RAG chưa conversational thật sự do chưa bơm history vào prompt: [src/services/rag/rag_service.py](src/services/rag/rag_service.py).
- `selected_file_ids` mới dừng ở lưu quan hệ, chưa tác động lên truy hồi chunk: [src/services/chat_service.py](src/services/chat_service.py).
- Xóa một file đơn lẻ chưa đồng bộ lại vector index (đang để note tạm bỏ qua): [src/services/file_service.py](src/services/file_service.py).
- Cách dùng decorator `require_role` chưa đồng nhất kiểu tham số (list/string): [src/core/auth.py](src/core/auth.py), [src/api/conversation/views.py](src/api/conversation/views.py).

## 5) Đề xuất ưu tiên cập nhật (mới)

### P0 (ưu tiên ngay để tăng chất lượng trả lời thật sự)

1. Q6: Đưa history thật từ DB vào `RAGService.chat_flow`, có giới hạn cửa sổ hội thoại.
2. Q8: Áp dụng filter retrieval theo `selected_file_ids` (và metadata scope/file_type nếu có).
3. Đồng bộ vector index khi xóa từng file (rebuild hoặc soft-delete metadata).
4. Chuẩn hóa lại role-check usage và contract response/error cho các API mới.

### P1 (tăng độ ổn định và khả năng nghiệm thu)

1. Q4: Cho phép cấu hình `chunk_size`/`chunk_overlap` qua API hoặc config theo conversation.
2. Q5: Bổ sung endpoint lấy citation theo response (ngoài việc trả kèm trong chat).
3. Bổ sung API smoke test + test tự động cho auth, upload, ask, history, clear.

### P2 (nâng cấp retrieval)

1. Q7: Hybrid search (BM25 + vector) với weighted score hoặc RRF.
2. Q9: Re-ranking với cross-encoder cho top-k kết quả.

### P3 (nâng cao)

1. Q10: Self-RAG (query rewrite, confidence scoring, fallback/multi-hop).

## 6) Mốc hoàn thành đề xuất (cập nhật)

- Milestone 1: Hoàn thành P0 cũ (API cơ bản + migration) -> **đã đạt phần lớn**.
- Milestone 2: Hoàn tất P0 mới + P1 (conversational history thật, retrieval filter, test cơ bản).
- Milestone 3: Hoàn tất P2 (hybrid + rerank) để tăng chất lượng retrieval.
- Milestone 4: Hoàn tất P3 (self-RAG) cho phần nâng cao.
