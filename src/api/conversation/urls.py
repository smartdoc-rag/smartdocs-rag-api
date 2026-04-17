from django.urls import path
from .views import ConversationCreateView, ConversationListView

urlpatterns = [
    path('', ConversationListView.as_view(), name='conversation-list'),
    path('create/', ConversationCreateView.as_view(), name='conversation-create'),
]