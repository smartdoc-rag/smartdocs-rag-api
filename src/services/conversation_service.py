from src.repositories.conversation_repository import ConversationRepository
from src.models.conversations import Conversation
from django.utils import timezone

class ConversationService:
    def __init__(self):
        self.conversation_repo = ConversationRepository()

    #tao session cua user
    def create_conversation(self, user_id: int, title: str = None) -> Conversation:
        if not user_id:
            raise ValueError("user_id is required")
        conv = Conversation(user_id=user_id, title=title, last_chat_at= timezone.now())
        return self.conversation_repo.create(conv)

    # lay session cua user
    def get_user_conversations(self, user_id: int, skip=0, limit=20):
        return self.conversation_repo.get_all(user_id=user_id, skip=skip, limit=limit)
    
    
    #update title
    def update_conversation(self, user_id: int, conversation_id: int, title: str = None) -> Conversation:
        if not user_id or not conversation_id:
            raise ValueError("user_id and conversation_id are required")
        
        conv = self.conversation_repo.get_user_conversation_by_id(user_id, conversation_id)
        if not conv:
            raise ValueError("Conversation not found")
        
        conv.title = title
        return self.conversation_repo.update(conv)
    

    #update last_chat
    def update_last_chat(self, user_id: int, conversation_id: int, title: str = None) -> Conversation:
        if not user_id or not conversation_id:
            raise ValueError("user_id and conversation_id are required")
        
        conv = self.conversation_repo.get_user_conversation_by_id(user_id, conversation_id)
        if not conv:
            raise ValueError("Conversation not found")
        
        conv.last_chat_at = timezone.now()
        return self.conversation_repo.update(conv)
    
    
    def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        if not user_id:
            raise ValueError("user_id is required")
        
        if not conversation_id:
            raise ValueError("conversation_id is required")
        
        conv = self.conversation_repo.get_user_conversation_by_id(user_id, conversation_id)
        
        if not conv:
            raise ValueError("Conversation not found")
        
        deleted_count = conv.delete()
        
        if not deleted_count:
            raise RuntimeError("Failed to delete conversation")
        
        return True
        

    #lay session theo id cua user
    def get_conversation_by_id(self, conversation_id: int, user_id: int):
        conv = self.conversation_repo.get_user_conversation_by_id(user_id, conversation_id)
        if not conv:
            raise PermissionError("Conversation not found or access denied")
        return conv
