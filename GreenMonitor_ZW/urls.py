from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.api.urls")),
    path("ee/", include("apps.earth_engine.urls")),
    path("vegetation/", include("apps.vegetation_analytics.urls")),
]
