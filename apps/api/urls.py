from django.urls import path
from . import views

urlpatterns = [
    path("api/vegetation/", views.vegetation_data, name="vegetation_data"),
]
