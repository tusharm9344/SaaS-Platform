from django.urls import path

from investigations.views import IncidentInvestigationsView


urlpatterns = [
    path(
        "incidents/<uuid:incident_id>/investigations/",
        IncidentInvestigationsView.as_view(),
        name="incident-investigations",
    ),
]