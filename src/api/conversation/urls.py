from django.urls import path
from .views import (
    ConversationCreateView, 
    ConversationListView, 
    ConversationUpdateView,
    ConversationPatchView, 
    ConversationDetailView,
    ConversationChunkConfigView,
    ConversationSelectedFilesView
)

urlpatterns = [
    path('', ConversationListView.as_view(), name='conversation-list'),
    path('<int:conversation_id>', ConversationDetailView.as_view()),
    path('create', ConversationCreateView.as_view(), name='conversation-create'),
    path('<int:conversation_id>/title', ConversationUpdateView.as_view(), name='conversation-update'),
    path('<int:conversation_id>/last-chat', ConversationPatchView.as_view(), name='conversation-last-chat'),
    path(
        "<int:conversation_id>/chunk-config",
        ConversationChunkConfigView.as_view(),
        name="chunk-config",
    ),
    path(
        "<int:conversation_id>/selected-files",
        ConversationSelectedFilesView.as_view(),
        name="conversation-selected-files"
    ),
]
