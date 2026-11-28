from uuid import uuid4

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import slugify

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from applications.models import (
    Application,
    ApplicationAPIKey,
    DiscoveredContainer,
    DiscoveryAgent,
    Service,
)

from applications.serializers import (
    ApplicationSerializer,
    ApplicationAPIKeySerializer,
    ContainerDiscoverySerializer,
    DiscoveredContainerSerializer,
    ServiceSerializer,
)

from applications.services.api_keys import (
    create_api_key,
    revoke_api_key,
    verify_api_key,
)

from incidents.services import detect_container_anomalies
from organizations.models import Membership


def get_user_organization_ids(user):
    return Membership.objects.filter(
        user=user
    ).values_list("organization_id", flat=True)


def get_application_membership(user, application):
    return get_object_or_404(
        Membership,
        user=user,
        organization_id=application.organization_id,
    )


def can_manage(membership):
    return membership.role in [
        Membership.Role.OWNER,
        Membership.Role.ADMIN,
    ]


class ApplicationListCreateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        applications = Application.objects.filter(
            organization_id__in=get_user_organization_ids(request.user)
        ).select_related("organization").order_by("-created_at")

        serializer = ApplicationSerializer(applications, many=True)

        return Response({
            "count": len(serializer.data),
            "results": serializer.data,
        })

    def post(self, request):
        organization_id = request.data.get("organization_id")

        if not organization_id:
            return Response(
                {"detail": "organization_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership = get_object_or_404(
            Membership.objects.select_related("organization"),
            user=request.user,
            organization_id=organization_id,
        )

        if not can_manage(membership):
            return Response(
                {"detail": "You do not have permission to create applications."},
                status=status.HTTP_403_FORBIDDEN,
            )

        name = request.data.get("name", "").strip()

        if not name:
            return Response(
                {"detail": "Application name is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        slug = slugify(request.data.get("slug") or name)

        if not slug:
            return Response(
                {"detail": "A valid application slug could not be generated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Application.objects.filter(
            organization=membership.organization,
            slug=slug,
        ).exists():
            return Response(
                {"detail": "An application with this slug already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        application = serializer.save(
            organization=membership.organization,
            slug=slug,
        )

        return Response(
            ApplicationSerializer(application).data,
            status=status.HTTP_201_CREATED,
        )


class ApplicationDetailView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_application(self, request, application_id):
        return get_object_or_404(
            Application.objects.select_related("organization"),
            id=application_id,
            organization_id__in=get_user_organization_ids(request.user),
        )

    def get(self, request, application_id):
        application = self.get_application(request, application_id)

        return Response(ApplicationSerializer(application).data)

    def patch(self, request, application_id):
        application = self.get_application(request, application_id)
        membership = get_application_membership(request.user, application)

        if not can_manage(membership):
            return Response(
                {"detail": "You do not have permission to update this application."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ApplicationSerializer(
            application,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class ApplicationAPIKeyListCreateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_application(self, request, application_id):
        return get_object_or_404(
            Application,
            id=application_id,
            organization_id__in=get_user_organization_ids(request.user),
        )

    def get(self, request, application_id):
        application = self.get_application(request, application_id)

        keys = application.api_keys.order_by("-created_at")

        serializer = ApplicationAPIKeySerializer(keys, many=True)

        return Response({
            "count": len(serializer.data),
            "results": serializer.data,
        })

    def post(self, request, application_id):
        application = self.get_application(request, application_id)
        membership = get_application_membership(request.user, application)

        if not can_manage(membership):
            return Response(
                {"detail": "You do not have permission to generate API keys."},
                status=status.HTTP_403_FORBIDDEN,
            )

        name = request.data.get("name", "Default key")

        if not isinstance(name, str) or not name.strip():
            return Response(
                {"detail": "A valid API key name is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(name.strip()) > 100:
            return Response(
                {"detail": "API key name must be at most 100 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        api_key, raw_key = create_api_key(
            application,
            name=name.strip(),
        )

        return Response(
            {
                "api_key": ApplicationAPIKeySerializer(api_key).data,
                "raw_key": raw_key,
                "message": "Copy this key now. It will not be displayed again.",
            },
            status=status.HTTP_201_CREATED,
        )


class ApplicationAPIKeyRevokeView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, application_id, api_key_id):
        application = get_object_or_404(
            Application,
            id=application_id,
            organization_id__in=get_user_organization_ids(request.user),
        )

        membership = get_application_membership(request.user, application)

        if not can_manage(membership):
            return Response(
                {"detail": "You do not have permission to revoke API keys."},
                status=status.HTTP_403_FORBIDDEN,
            )

        api_key = get_object_or_404(
            ApplicationAPIKey,
            id=api_key_id,
            application=application,
        )

        if not api_key.is_active or api_key.revoked_at:
            return Response(
                {"detail": "This API key has already been revoked."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        revoke_api_key(api_key)

        return Response({
            "success": True,
            "message": "API key revoked successfully.",
        })


class ServiceListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        services = Service.objects.filter(
            application__organization_id__in=get_user_organization_ids(request.user)
        ).select_related("application")

        serializer = ServiceSerializer(services, many=True)

        return Response(serializer.data)


class ServiceDetailView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_service(self, request, service_id):
        return get_object_or_404(
            Service.objects.select_related("application"),
            id=service_id,
            application__organization_id__in=get_user_organization_ids(request.user),
        )

    def get(self, request, service_id):
        service = self.get_service(request, service_id)

        return Response(ServiceSerializer(service).data)

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

        return Response(ServiceSerializer(service).data)


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

                container, created = DiscoveredContainer.objects.update_or_create(
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

                detect_container_anomalies(container)

                results.append({
                    "container_id": container.container_id,
                    "name": container.name,
                    "service": service.name,
                    "created": created,
                })

            DiscoveredContainer.objects.filter(
                application=application,
                agent=agent,
            ).exclude(
                container_id__in=container_ids
            ).exclude(
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
        containers = (
            DiscoveredContainer.objects.filter(
                application__organization_id__in=get_user_organization_ids(request.user),
                is_monitored=True,
            )
            .select_related("application", "service", "agent")
            .order_by("-last_seen")
        )

        serializer = DiscoveredContainerSerializer(containers, many=True)

        return Response({
            "count": len(serializer.data),
            "containers": serializer.data,
        })