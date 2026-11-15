from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from applications.models import Service
from applications.serializers import ServiceSerializer
from organizations.models import Membership


class ServiceListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization_ids = Membership.objects.filter(
            user=request.user
        ).values_list("organization_id", flat=True)
        services = Service.objects.filter(
            application__organization_id__in=organization_ids
        ).select_related("application")
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)


class ServiceDetailView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_service(self, request, service_id):
        organization_ids = Membership.objects.filter(
            user=request.user
        ).values_list("organization_id", flat=True)
        return get_object_or_404(
            Service.objects.select_related("application"),
            id=service_id,
            application__organization_id__in=organization_ids,
        )

    def get(self, request, service_id):
        service = self.get_service(request, service_id)
        serializer = ServiceSerializer(service)
        return Response(serializer.data)

    def patch(self, request, service_id):
        service = self.get_service(request, service_id)
        if "is_active" not in request.data:
            return Response(
                {"error": "is_active field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(request.data["is_active"], bool):
            return Response(
                {"error": "is_active must be a boolean."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        service.is_active = request.data["is_active"]
        service.save(update_fields=["is_active"])
        serializer = ServiceSerializer(service)
        return Response(serializer.data)
