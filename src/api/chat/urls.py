from django.urls import path
from .views import ChatAskView, ChatHistoryView, ClearHistoryView

urlpatterns = [
    path('<int:conversation_id>/ask/', ChatAskView.as_view(), name='chat-ask'),
    path('<int:conversation_id>/history/', ChatHistoryView.as_view(), name='chat-history'),
    path('<int:conversation_id>/clear-history/', ClearHistoryView.as_view(), name='clear-history'),
]