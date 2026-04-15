"""
URL configuration for src project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path, include
from src.api.department.views import DepartmentView

urlpatterns = [
    path("api/auth/", include("src.api.auth.urls")),
    path("api/users/", include("src.api.user.urls")),
    # List endpoint without trailing slash
    path("api/departments", DepartmentView.as_view()),
    # Include detail endpoints with slash
    path("api/departments/", include("src.api.department.urls")),
]
