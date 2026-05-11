from django.urls import path
from . import views

urlpatterns = [
    path("a/", views.home, name="home"),
    path("chirps/", views.chirps_map, name="chirps_map"),
]
