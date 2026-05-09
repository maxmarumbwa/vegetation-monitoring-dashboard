from django.urls import path
from . import views

urlpatterns = [
    path("", views.chirps_map, name="chirps_map"),
    path("test/", views.get_rainfall_tile, name="get_rainfall_tile"),
    path("chirps/", views.chirps_map, name="chirps_map"),
]
