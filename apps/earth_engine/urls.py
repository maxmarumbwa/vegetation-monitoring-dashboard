from django.urls import path
from . import views

urlpatterns = [
    path("ee/auth/", views.auth, name="auth"),
]
