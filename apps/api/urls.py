from django.urls import path
from apps.api import views
from django.views.generic import TemplateView

urlpatterns = [
    path(
        "",
        views.home,
        name="home",
    ),
    path(
        "dashboard/",
        views.dashboard,
        name="dashboard",
    ),
    path(
        "get_ndvi_anomaly_timeseries/",
        views.get_ndvi_anomaly_timeseries,
        name="get_ndvi_anomaly_timeseries",
    ),
    path(
        "get_ndvi_layers_start_end/",
        views.get_ndvi_layers_start_end,
        name="get_ndvi_layers_start_end",
    ),
]
