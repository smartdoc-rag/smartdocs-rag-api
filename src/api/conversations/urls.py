from django.urls import path
from .views import (
    ConversationListView,
    ConversationDetailView,
    ConversationMessagesView,
)

urlpatterns = [
    # Conversations
    path("", ConversationListView.as_view(), name="conversation-list"),
    path("<int:conversation_id>/", ConversationDetailView.as_view(), name="conversation-detail"),
    
    # Messages trong conversation
    path("<int:conversation_id>/messages/", ConversationMessagesView.as_view(), name="conversation-messages"),
]