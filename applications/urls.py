from django.urls import path

from applications.views import ServiceDetailView, ServiceListView
from applications.views import ContainerListView
from applications.views import ContainerDiscoveryView
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
    path(
        "containers/discover/",
    ContainerDiscoveryView.as_view(),
    name="container-discovery",
    ),
    path("containers/", ContainerListView.as_view(), name="container-list"),
]
