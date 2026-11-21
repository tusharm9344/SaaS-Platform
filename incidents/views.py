from django.db.models import Count
from rest_framework import generics, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from incidents.models import Incident
from incidents.serializers import (
    IncidentSerializer,
    IncidentDetailSerializer,
    InvestigationSerializer,
)


class IncidentPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class IncidentBaseView:

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only retrieve incidents belonging to organizations
        # where the authenticated user is a member.

        from organizations.models import Membership

        organization_ids = Membership.objects.filter(
            user=self.request.user
        ).values_list("organization_id", flat=True)

        return Incident.objects.filter(
            application__organization_id__in=organization_ids
        ).select_related(
            "application",
            "service",
        )


class IncidentListView(IncidentBaseView, generics.ListAPIView):

    serializer_class = IncidentSerializer
    pagination_class = IncidentPagination

    def get_queryset(self):
        queryset = super().get_queryset()

        incident_status = self.request.query_params.get("status")
        service_id = self.request.query_params.get("service")
        environment = self.request.query_params.get("environment")
        application_id = self.request.query_params.get("application")

        if incident_status:
            queryset = queryset.filter(status=incident_status.lower())

        if service_id:
            queryset = queryset.filter(service_id=service_id)

        if environment:
            queryset = queryset.filter(
                service__environment=environment.lower()
            )

        if application_id:
            queryset = queryset.filter(
                application_id=application_id
            )

        return queryset.order_by("-last_seen")


class IncidentDetailView(
    IncidentBaseView,
    generics.RetrieveAPIView,
):

    serializer_class = IncidentDetailSerializer
    lookup_url_kwarg = "incident_id"


class InvestigationDetailView(IncidentBaseView, APIView):

    def get(self, request, incident_id):

        incident = generics.get_object_or_404(
            self.get_queryset(),
            id=incident_id,
        )

        investigation = getattr(
            incident,
            "investigation",
            None,
        )

        if investigation is None:
            return Response(
                {"detail": "Investigation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = InvestigationSerializer(investigation)

        return Response(serializer.data)


class IncidentStatusView(IncidentBaseView, APIView):

    new_status = None

    def post(self, request, incident_id):

        incident = generics.get_object_or_404(
            self.get_queryset(),
            id=incident_id,
        )

        incident.status = self.new_status
        incident.save(update_fields=["status", "updated_at"])

        return Response(
            IncidentSerializer(incident).data,
            status=status.HTTP_200_OK,
        )


class ResolveIncidentView(IncidentStatusView):
    new_status = "resolved"


class ReopenIncidentView(IncidentStatusView):
    new_status = "open"


class IgnoreIncidentView(IncidentStatusView):
    new_status = "ignored"