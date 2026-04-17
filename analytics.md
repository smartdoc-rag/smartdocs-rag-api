# Phân tích hiện trạng SmartDoc RAG API (Django backend cho React)

## 1) Phạm vi kiểm tra

- Nguồn đối chiếu yêu cầu: [assignment.md](assignment.md) (mục 8.2.1 -> 8.2.10).
- Nguồn đối chiếu hiện trạng: toàn bộ mã trong workspace, không đọc thư mục .venv.
- Bối cảnh triển khai: frontend dùng React, nên backend cần hoàn chỉnh ở dạng REST API có thể gọi độc lập.

## 2) Thang trọng số đánh giá

- Trọng số tổng: 100.
- Có thêm hạng mục A0 (API readiness) vì đây là điều kiện bắt buộc khi FE là React.
- Cách tính điểm đạt: Trọng số x Mức hoàn thành.

| Mã | Hạng mục | Trọng số | Trạng thái | Mức hoàn thành | Điểm đạt | Minh chứng chính |
|---|---|---:|---|---:|---:|---|
| A0 | Đóng gói backend thành API hoàn chỉnh cho React (ngoài auth/user phải có file/upload/chat/history/citation API) | 25 | Chưa đạt | 20% | 5.0 | Route hiện chỉ có [src/urls.py](src/urls.py#L21), [src/urls.py](src/urls.py#L22) |
| Q1 | Hỗ trợ file DOCX | 6 | Làm một phần | 15% | 0.9 | Có kiểu file docx tại [src/models/files.py](src/models/files.py#L19), chưa có loader/API DOCX |
| Q2 | Lưu lịch sử hội thoại | 8 | Làm một phần | 35% | 2.8 | Có model/repository: [src/models/conversations.py](src/models/conversations.py), [src/models/request_messages.py](src/models/request_messages.py), [src/models/response_messages.py](src/models/response_messages.py), [src/repositories/request_message_repository.py](src/repositories/request_message_repository.py), [src/repositories/response_message_repository.py](src/repositories/response_message_repository.py) |
| Q3 | Clear History + Clear Vector Store | 5 | Chưa làm | 0% | 0.0 | Không có endpoint/service xóa lịch sử hoặc vector store |
| Q4 | Cải thiện chunk strategy | 7 | Làm một phần | 30% | 2.1 | Có tham số chunk trong [src/services/rag/file_ingestion_service.py](src/services/rag/file_ingestion_service.py#L21), [src/services/rag/file_ingestion_service.py](src/services/rag/file_ingestion_service.py#L34), [src/services/rag/file_ingestion_service.py](src/services/rag/file_ingestion_service.py#L35) |
| Q5 | Citation/source tracking | 8 | Làm một phần | 25% | 2.0 | Có schema citation: [src/models/message_citations.py](src/models/message_citations.py), [src/repositories/message_citation_repository.py](src/repositories/message_citation_repository.py) |
| Q6 | Conversational RAG | 10 | Làm một phần | 20% | 2.0 | Prompt có biến history tại [src/core/rag/prompt.py](src/core/rag/prompt.py#L15), [src/core/rag/prompt.py](src/core/rag/prompt.py#L29) nhưng đang truyền rỗng ở [src/services/rag/rag_service.py](src/services/rag/rag_service.py#L25) |
| Q7 | Hybrid search (semantic + BM25) | 8 | Chưa làm | 0% | 0.0 | Chưa có BM25/ensemble; retriever hiện chỉ similarity ở [src/services/rag/file_ingestion_service.py](src/services/rag/file_ingestion_service.py#L46) |
| Q8 | Multi-document + metadata filtering | 10 | Làm một phần | 20% | 2.0 | Có mô hình file/scope/chọn file: [src/models/files.py](src/models/files.py), [src/models/request_selected_files.py](src/models/request_selected_files.py), nhưng chưa có retrieval filter API |
| Q9 | Re-ranking với Cross-Encoder | 7 | Chưa làm | 0% | 0.0 | Chưa có lớp reranker/cross-encoder trong src |
| Q10 | Self-RAG (query rewrite, confidence, multi-hop) | 6 | Chưa làm | 0% | 0.0 | Chưa có flow self-evaluation/rewrite/scoring |

**Tổng điểm hiện tại (ước tính): 16.8 / 100**

## 3) Các chức năng đã làm được và chưa làm được

### Đã làm được (hoặc có nền tảng)

- Có khung Django REST cho auth/user: [src/api/auth/views.py](src/api/auth/views.py), [src/api/user/views.py](src/api/user/views.py).
- Có khung RAG cơ bản ở mức service: ingest + splitter + FAISS retriever + prompt song ngữ: [src/services/rag/file_ingestion_service.py](src/services/rag/file_ingestion_service.py), [src/services/rag/rag_service.py](src/services/rag/rag_service.py), [src/core/rag/prompt.py](src/core/rag/prompt.py).
- Có thiết kế dữ liệu cho conversation, file, request/response message, citation, selected file.

### Chưa làm được hoặc chưa hoàn thiện

- Chưa API hóa luồng RAG cho React (upload file, tạo conversation, chat, lấy lịch sử, lấy citation).
- Chưa có migration thực tế để đưa schema vào DB; cấu hình migration có tại [src/settings.py](src/settings.py#L125) nhưng thư mục [src/migrations](src/migrations) hiện chỉ có __init__.py.
- Chưa có test tự động cho các luồng chính.

## 4) Blocker kỹ thuật cần sửa ngay (ảnh hưởng chức năng hiện có)

- Lệch tên field mật khẩu giữa model và service:
	- Model dùng password_hash tại [src/models/user.py](src/models/user.py#L8).
	- Service lại dùng hashed_password tại [src/services/auth_service.py](src/services/auth_service.py#L46), [src/services/auth_service.py](src/services/auth_service.py#L54), [src/services/auth_service.py](src/services/auth_service.py#L108), [src/services/auth_service.py](src/services/auth_service.py#L110).
- Luồng role không khớp model:
	- Kiểm tra role ở [src/core/auth.py](src/core/auth.py#L36), serialize role ở [src/api/user/UserResponse.py](src/api/user/UserResponse.py#L9), và so sánh role ở [src/services/user_service.py](src/services/user_service.py#L45).
	- Nhưng User model hiện không có cột role trong [src/models/user.py](src/models/user.py).
- Sai tên hàm service tại API user:
	- View gọi get_users ở [src/api/user/views.py](src/api/user/views.py#L16).
	- Service chỉ có get_all ở [src/services/user_service.py](src/services/user_service.py#L17).
- Sai kiểu đối số khi delete:
	- Service truyền id vào delete ở [src/services/user_service.py](src/services/user_service.py#L39).
	- Repository base cần object model tại [src/repositories/base.py](src/repositories/base.py#L38).

## 5) Đề xuất thứ tự ưu tiên (trước -> sau)

### P0 (làm trước, bắt buộc để backend chạy ổn định)

1. Sửa toàn bộ blocker ở mục 4.
2. Tạo migrations đầy đủ cho src.models và chạy migrate ổn định dev/prod.
3. Chuẩn hóa API contract cho React: auth, users, conversations, files, chat, citations.

### P1 (ưu tiên cao, bám sát yêu cầu dễ lấy điểm và tạo sản phẩm chạy được)

1. Q2 Lưu lịch sử hội thoại: implement service + endpoint create/list conversation và message.
2. Q1 Hỗ trợ DOCX: thêm loader (python-docx hoặc Docx loader), validate upload, ingest vào pipeline hiện tại.
3. Q3 Clear history/vector store: endpoint xóa có xác nhận từ FE.
4. Q5 Citation/source tracking: lưu page/chunk/score khi trả lời và trả về trong response API.
5. Q4 Chunk strategy: cho phép cấu hình chunk_size/chunk_overlap qua API, lưu cấu hình theo conversation hoặc request.

### P2 (trung hạn, nâng chất lượng trả lời)

1. Q6 Conversational RAG: thay history rỗng bằng history thật từ DB, giới hạn cửa sổ ngữ cảnh.
2. Q8 Multi-document + metadata filtering: upload nhiều file, filter theo file/scope/type/date.
3. Q7 Hybrid search: thêm BM25 + vector, kết hợp điểm (weighted/rrf).

### P3 (nâng cao, tối ưu chất lượng học thuật)

1. Q9 Re-ranking với cross-encoder.
2. Q10 Self-RAG (query rewrite, confidence scoring, multi-hop).

## 6) Mốc hoàn thành đề xuất

- Milestone 1: Hoàn tất P0 + API smoke test (React gọi được toàn bộ luồng cơ bản).
- Milestone 2: Hoàn tất P1 (đạt chức năng cốt lõi theo assignment).
- Milestone 3: Hoàn tất P2 (chất lượng retrieval tốt hơn, hỗ trợ multi-document).
- Milestone 4: Hoàn tất P3 (nâng cao, tối ưu điểm phần khó).
