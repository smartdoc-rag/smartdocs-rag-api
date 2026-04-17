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