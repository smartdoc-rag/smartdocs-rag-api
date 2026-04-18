from django.urls import path
from .views import ConversationCreateView, ConversationListView, ConversationChunkConfigView

urlpatterns = [
    path('', ConversationListView.as_view(), name='conversation-list'),
    path('create/', ConversationCreateView.as_view(), name='conversation-create'),
    path('<int:conversation_id>/chunk-config/', ConversationChunkConfigView.as_view(), name='chunk-config'),
]
