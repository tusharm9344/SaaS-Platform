from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from incidents.services import detect_container_anomalies
from applications.models import DiscoveredContainer, DiscoveryAgent, Service
from applications.services.api_keys import verify_api_key
from applications.serializers import (
    ContainerDiscoverySerializer,
    DiscoveredContainerSerializer,
    ServiceSerializer,
)
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


class ContainerDiscoveryView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        raw_key = request.headers.get("X-API-Key", "")
        api_key = verify_api_key(raw_key)

        if api_key is None:
            return Response(
                {"error": "Invalid or revoked API key."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        application = api_key.application

        if not application.is_active:
            return Response(
                {"error": "Application is inactive."},
                status=status.HTTP_403_FORBIDDEN,
            )

        agent_id = request.data.get("agent_id")
        hostname = request.data.get("hostname")

        if not isinstance(agent_id, str) or not agent_id.strip():
            return Response(
                {"error": "agent_id must be a non-empty string."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(agent_id.strip()) > 64:
            return Response(
                {"error": "agent_id must be at most 64 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(hostname, str) or not hostname.strip():
            return Response(
                {"error": "hostname must be a non-empty string."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(hostname.strip()) > 255:
            return Response(
                {"error": "hostname must be at most 255 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(request.data.get("containers"), list):
            return Response(
                {"error": "containers must be a list."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(request.data["containers"]) > 500:
            return Response(
                {"error": "Maximum 500 containers per request."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        agent_id = agent_id.strip()
        hostname = hostname.strip()
        results = []
        container_ids = []
        now = timezone.now()

        with transaction.atomic():
            agent, created_agent = DiscoveryAgent.objects.update_or_create(
                application=application,
                agent_id=agent_id,
                defaults={
                    "hostname": hostname,
                    "last_heartbeat": now,
                    "is_active": True,
                },
            )
            for item in request.data["containers"]:
                serializer = ContainerDiscoverySerializer(data=item)
                serializer.is_valid(raise_exception=True)

                data = serializer.validated_data
                container_ids.append(data["container_id"])

                service, _ = Service.objects.get_or_create(
                    application=application,
                    name=data["service_name"],
                    environment=data["environment"],
                )
                service.last_seen = now
                service.is_active = True
                service.save(update_fields=["last_seen", "is_active"])

                container, created = (
                    DiscoveredContainer.objects.update_or_create(
                        application=application,
                        container_id=data["container_id"],
                        defaults={
                            "agent": agent,
                            "service": service,
                            "name": data["name"],
                            "image": data["image"],
                            "status": data["status"],
                            "health_status": data.get("health_status"),
                            "cpu_percent": data.get("cpu_percent"),
                            "memory_usage": data.get("memory_usage"),
                            "memory_limit": data.get("memory_limit"),
                            "memory_percent": data.get("memory_percent"),
                            "metrics_updated_at": now,
                            "labels": data["labels"],
                            "last_seen": now,
                        },
                    )
                )
                detect_container_anomalies(container)

                results.append(
                    {
                        "container_id": container.container_id,
                        "name": container.name,
                        "service": service.name,
                        "created": created,
                    }
                )

            DiscoveredContainer.objects.filter(
                application=application,
                agent=agent,
            ).exclude(container_id__in=container_ids).exclude(
                status="removed"
            ).update(status="removed")

        return Response(
            {
                "status": "success",
                "agent_id": agent.agent_id,
                "hostname": agent.hostname,
                "agent_created": created_agent,
                "discovered": len(results),
                "containers": results,
            },
            status=status.HTTP_200_OK,
        )


class ContainerListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization_ids = Membership.objects.filter(
            user=request.user
        ).values_list("organization_id", flat=True)
        containers = (
            DiscoveredContainer.objects.filter(
                application__organization_id__in=organization_ids,
                is_monitored=True,
            )
            .select_related("application", "service", "agent")
            .order_by("-last_seen")
        )
        serializer = DiscoveredContainerSerializer(
            containers,
            many=True,
        )
        return Response(
            {
                "count": len(serializer.data),
                "containers": serializer.data,
            }
        )