from django.urls import path

from applications.views import (
    ApplicationListCreateView,
    ApplicationDetailView,
    ApplicationAPIKeyListCreateView,
    ApplicationAPIKeyRevokeView,
    ServiceDetailView,
    ServiceListView,
    ContainerListView,
    ContainerDiscoveryView,
)

urlpatterns = [
    path(
        "applications/",
        ApplicationListCreateView.as_view(),
        name="application-list-create",
    ),
    path(
        "applications/<uuid:application_id>/",
        ApplicationDetailView.as_view(),
        name="application-detail",
    ),
    path(
        "applications/<uuid:application_id>/api-keys/",
        ApplicationAPIKeyListCreateView.as_view(),
        name="application-api-keys",
    ),
    path(
        "applications/<uuid:application_id>/api-keys/<uuid:api_key_id>/revoke/",
        ApplicationAPIKeyRevokeView.as_view(),
        name="application-api-key-revoke",
    ),
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
    path(
        "containers/",
        ContainerListView.as_view(),
        name="container-list",
    ),
]