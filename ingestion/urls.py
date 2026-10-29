
from django.urls import path
from ingestion.views import ErrorIngestionView

urlpatterns = [
    path("events/", ErrorIngestionView.as_view(), name="ingest-error-event"),
]