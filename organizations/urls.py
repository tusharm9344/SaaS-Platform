from django.urls import path

from organizations.views import (
    AIProviderConfigView,
    AIProviderTestView,
    OrganizationListView,
)

urlpatterns = [
    path(
        "organizations/",
        OrganizationListView.as_view(),
        name="organization-list",
    ),
    path(
        "organizations/<uuid:organization_id>/ai-provider/",
        AIProviderConfigView.as_view(),
        name="ai-provider-config",
    ),
    path(
        "organizations/<uuid:organization_id>/ai-provider/test/",
        AIProviderTestView.as_view(),
        name="ai-provider-test",
    ),
]