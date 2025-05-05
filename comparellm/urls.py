from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("return-status/", views.return_status, name="return_status"),
    path("query/<str:label>/<path:model>/", views.query_detail, name="query_detail"),
    path(
        "return-staus-summary/",
        views.return_status_summary,
        name="return_status_summary",
    ),
    path("layer-comparison/", views.layer_comparison, name="layer_comparison"),
    path(
        "layer-comparison-summary/",
        views.layer_comparison_summary,
        name="layer_comparison_summary",
    ),
    path("merged-summary/", views.merged_summary, name="merged_summary"),
    path("model-rankings/", views.model_rankings, name="model_rankings"),
    path(
        "model-correctness-rankings/",
        views.model_correctness_rankings,
        name="model_correctness_rankings",
    ),
]
