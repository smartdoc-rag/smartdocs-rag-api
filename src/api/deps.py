from src.core.rag.cross_encoder import CrossEncoderReranker
from src.repositories.chunk_repository import ChunkRepository
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.file_repository import FileRepository
from src.repositories.message_citation_repository import MessageCitationRepository
from src.repositories.message_stat_repository import MessageStatRepository
from src.repositories.request_message_repository import RequestMessageRepository
from src.repositories.file_repository import FileRepository
from src.repositories.conversation_repository import ConversationRepository
from src.services.conversation_service import ConversationService
from src.services.file_service import FileService
from src.services.rag.file_ingestion_service import FileIngestionService
from src.repositories.request_selected_file_repository import (
    RequestSelectedFileRepository,
)
from src.repositories.response_message_repository import ResponseMessageRepository
from src.services.auth_service import AuthService
from src.services.chat_service import ChatService
from src.services.rag.file_ingestion_service import FileIngestionService
from src.services.user_service import UserService
from src.repositories.user_repository import UserRepository
from src.repositories.token_repository import TokenRepository


def auth_service() -> AuthService:
    return AuthService(user_repo=UserRepository(), token_repo=TokenRepository())


def user_service() -> UserService:
    return UserService(user_repo=UserRepository())


def chat_service() -> ChatService:
    return ChatService(
        conv_repo=ConversationRepository(),
        req_repo=RequestMessageRepository(),
        resp_repo=ResponseMessageRepository(),
        file_repo=FileRepository(),
        selected_repo=RequestSelectedFileRepository(),
        citation_repo=MessageCitationRepository(),
        stat_repo=MessageStatRepository(),
        ingestion_service=FileIngestionService(),
        reranker=CrossEncoderReranker(),
    )


def conversation_service() -> ConversationService:
    return ConversationService(conversation_repo=ConversationRepository())


def file_service() -> FileService:
    return FileService(
        file_repo=FileRepository(),
        conversation_repo=ConversationRepository(),
        chunk_repo=ChunkRepository(),
        ingestion_service=FileIngestionService(),
    )
