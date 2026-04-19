from django.urls import path
from .views import (
    ConversationCreateView, 
    ConversationListView, 
    ConversationUpdateView,
    ConversationPatchView, 
    ConversationDeleteView,    
    ConversationChunkConfigView
)

urlpatterns = [
    path('', ConversationListView.as_view(), name='conversation-list'),
    path('create', ConversationCreateView.as_view(), name='conversation-create'),
    path('<int:conversation_id>/title', ConversationUpdateView.as_view(), name='conversation-update'),
    path('<int:conversation_id>/last-chat', ConversationPatchView.as_view(), name='conversation-last-chat'),
    path('<int:conversation_id>', ConversationDeleteView.as_view(), name='conversation-delete'),
    path(
        "<int:conversation_id>/chunk-config/",
        ConversationChunkConfigView.as_view(),
        name="chunk-config",
    ),

]
