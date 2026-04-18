from src.repositories.conversation_repository import ConversationRepository
from src.models.conversations import Conversation

class ConversationService:
    def __init__(self):
        self.conversation_repo = ConversationRepository()

    #tao session cua user
    def create_conversation(self, user_id: int, title: str = None) -> Conversation:
        if not user_id:
            raise ValueError("user_id is required")
        conv = Conversation(user_id=user_id, title=title)
        return self.conversation_repo.create(conv)

    # lay session cua user
    def get_user_conversations(self, user_id: int, skip=0, limit=20):
        return self.conversation_repo.get_all(user_id=user_id, skip=skip, limit=limit)

    #lay session theo id cua user
    def get_conversation_by_id(self, conversation_id: int, user_id: int):
        conv = self.conversation_repo.get_user_conversation_by_id(user_id, conversation_id)
        if not conv:
            raise PermissionError("Conversation not found or access denied")
        return conv