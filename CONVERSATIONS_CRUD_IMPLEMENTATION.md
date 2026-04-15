# Conversations CRUD Implementation

Đã hoàn thành việc triển khai CRUD cơ bản cho conversations theo kiến trúc layered architecture như trong tài liệu `lite-django-layered-architecture-setup.md`.

## Các thành phần đã thêm

### 1. Models
- **Conversation**: Lưu trữ hội thoại giữa người dùng và hệ thống
  - `title`: Tiêu đề hội thoại (có thể null)
  - `user`: ForeignKey đến User
  - `is_active`: Trạng thái active (soft delete)
  
- **Message**: Lưu trữ từng message trong conversation
  - `conversation`: ForeignKey đến Conversation
  - `user`: ForeignKey đến User (người gửi)
  - `content`: Nội dung message
  - `role`: Vai trò (user/assistant/system)

### 2. Repositories
- **ConversationRepository**: CRUD + methods đặc biệt
  - `get_by_id_with_messages()`: Eager load messages
  - `get_user_conversations()`: Lấy conversations của user
  - `get_conversation_with_user_check()`: Kiểm tra quyền truy cập
  
- **MessageRepository**: CRUD + methods đặc biệt
  - `get_conversation_messages()`: Lấy messages của conversation
  - `create_message_batch()`: Tạo nhiều messages cùng lúc

### 3. Service Layer
- **ConversationService**: Business logic cho conversations
  - `create_conversation()`: Tạo conversation mới
  - `get_user_conversations()`: Lấy danh sách conversations của user
  - `get_conversation()`: Lấy conversation + kiểm tra quyền
  - `update_conversation_title()`: Cập nhật tiêu đề
  - `delete_conversation()`: Soft delete (is_active=False)
  - `add_message()`: Thêm message vào conversation
  - `get_conversation_messages()`: Lấy messages của conversation

### 4. API Layer
**Endpoints:**
- `GET /api/conversations/` - Lấy danh sách conversations của user
- `POST /api/conversations/` - Tạo conversation mới
- `GET /api/conversations/{id}/` - Lấy chi tiết conversation kèm messages
- `PUT /api/conversations/{id}/` - Cập nhật tiêu đề conversation
- `DELETE /api/conversations/{id}/` - Xóa conversation (soft delete)
- `GET /api/conversations/{id}/messages/` - Lấy danh sách messages
- `POST /api/conversations/{id}/messages/` - Thêm message vào conversation

**Request/Response schemas:**
- `CreateConversationRequest`: {title?}
- `UpdateConversationRequest`: {title}
- `AddMessageRequest`: {content, role?}
- `ConversationResponse`: Full conversation data + messages
- `MessageResponse`: Message data

## Kiến trúc tuân thủ
- **Layered Architecture**: API → Service → Repository → Model
- **Dependency Injection**: Service nhận repository qua constructor
- **Request/Response Pattern**: Tách biệt validation và serialization
- **Error Handling**: Sử dụng custom exceptions với message tiếng Việt
- **Pagination**: Hỗ trợ phân trang cho danh sách
- **Authorization**: @require_auth decorator cho tất cả endpoints

## Cần làm tiếp
1. **Tạo migrations**: Chạy `python manage.py makemigrations models` và `python manage.py migrate`
2. **Testing**: Viết unit tests cho service và integration tests cho API
3. **Documentation**: Thêm API documentation với Swagger/OpenAPI
4. **Validation**: Thêm validation cho content length, rate limiting

## Cách sử dụng
```bash
# Tạo conversation
POST /api/conversations/
{
  "title": "Hỏi về Django"
}

# Lấy danh sách conversations
GET /api/conversations/?page=1&page_size=20

# Thêm message
POST /api/conversations/1/messages/
{
  "content": "Xin chào, tôi cần hỗ trợ",
  "role": "user"
}
```

Code đã được commit trên nhánh `feature/conversations-crud` và sẵn sàng để merge.