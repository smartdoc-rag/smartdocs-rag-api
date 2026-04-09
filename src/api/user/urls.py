from django.urls import path
from src.api.user.views import UserListView, UserDetailView, BlockUserView

urlpatterns = [
    path("", UserListView.as_view()),
    path("<int:user_id>", UserDetailView.as_view()),
    path("<int:user_id>/block", BlockUserView.as_view()),
]
