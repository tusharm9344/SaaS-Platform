from django.shortcuts import render

# Create your views here.
from django.shortcuts import get_object_or_404

from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from incidents.models import Incident
from investigations.models import Investigation
from investigations.serializers import InvestigationSerializer


class IncidentInvestigationsView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, incident_id):
        incident = get_object_or_404(
            Incident.objects.filter(
                application__organization__memberships__user=request.user
            ).distinct(),
            id=incident_id,
        )

        investigations = Investigation.objects.filter(
            incident=incident
        ).order_by("-created_at")

        serializer = InvestigationSerializer(
            investigations,
            many=True,
        )

        return Response({
            "incident_id": str(incident.id),
            "investigations": serializer.data,
        })