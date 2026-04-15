from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.services.conversation_service import ConversationService
from src.repositories.user_repository import UserRepository
from src.repositories.token_repository import TokenRepository
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.conversation_message_repository import ConversationMessageRepository
from src.repositories.document_repository import DocumentRepository


def auth_service() -> AuthService:
    return AuthService(user_repo=UserRepository(), token_repo=TokenRepository())


def user_service() -> UserService:
    return UserService(user_repo=UserRepository())


def get_conversation_service() -> ConversationService:
    return ConversationService(
        conversation_repo=ConversationRepository(),
        message_repo=ConversationMessageRepository(),
        user_repo=UserRepository(),
        document_repo=DocumentRepository()
    )
