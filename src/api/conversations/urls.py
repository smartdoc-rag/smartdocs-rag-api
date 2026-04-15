from django.urls import path
from src.api.conversations.views import (
    ConversationListView,
    ConversationDetailView,
    ConversationMessagesView,
)

urlpatterns = [
    # Conversations
    path("", ConversationListView.as_view(), name="conversation-list"),
    path("<int:conversation_id>/", ConversationDetailView.as_view(), name="conversation-detail"),
    path("<int:conversation_id>/messages/", ConversationMessagesView.as_view(), name="conversation-messages"),
]