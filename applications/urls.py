from django.urls import path

from applications.views import ServiceDetailView, ServiceListView


urlpatterns = [
    path(
        "services/",
        ServiceListView.as_view(),
        name="service-list",
    ),
    path(
        "services/<uuid:service_id>/",
        ServiceDetailView.as_view(),
        name="service-detail",
    ),
]
