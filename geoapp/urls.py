from django.urls import path
from . import views

app_name = "geoapp"

urlpatterns = [
    path("", views.default_map, name="default_map"),
]
