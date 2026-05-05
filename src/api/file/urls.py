from django.urls import path

from .views import FileUploadView, FileListView, FileDeleteView, ClearFilesView

urlpatterns = [
    path('<int:conversation_id>/upload/', FileUploadView.as_view(), name='file-upload'),
    path('<int:conversation_id>/files/', FileListView.as_view(), name='file-list'),
    path('<int:conversation_id>/files/<int:file_id>/delete/', FileDeleteView.as_view(), name='file-delete'),
    path('<int:conversation_id>/clear-files/', ClearFilesView.as_view(), name='clear-files'),
    path('<int:conversation_id>/file/', FileDeleteView.as_view(), name='file'),

]