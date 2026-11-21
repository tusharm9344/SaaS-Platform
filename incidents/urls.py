from django.urls import path

from incidents.views import (
    IncidentListView,
    IncidentDetailView,
    InvestigationDetailView,
    ResolveIncidentView,
    ReopenIncidentView,
    IgnoreIncidentView,
)

urlpatterns = [
    path(
        "",
        IncidentListView.as_view(),
        name="incident-list",
    ),

    path(
        "<uuid:incident_id>/",
        IncidentDetailView.as_view(),
        name="incident-detail",
    ),

    path(
        "<uuid:incident_id>/investigation/",
        InvestigationDetailView.as_view(),
        name="incident-investigation",
    ),

    path(
        "<uuid:incident_id>/resolve/",
        ResolveIncidentView.as_view(),
        name="incident-resolve",
    ),

    path(
        "<uuid:incident_id>/reopen/",
        ReopenIncidentView.as_view(),
        name="incident-reopen",
    ),

    path(
        "<uuid:incident_id>/ignore/",
        IgnoreIncidentView.as_view(),
        name="incident-ignore",
    ),
]