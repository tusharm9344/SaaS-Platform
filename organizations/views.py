import json
import logging

from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.models import Membership, Organization, AIProviderConfig
from organizations.crypto import encrypt_api_key, decrypt_api_key
from investigations.clients.ai import generate_completion

logger = logging.getLogger(__name__)


class AIProviderConfigView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_membership(self, request, organization_id):
        return get_object_or_404(
            Membership.objects.select_related("organization"),
            user=request.user,
            organization_id=organization_id,
        )

    def get(self, request, organization_id):
        membership = self.get_membership(
            request,
            organization_id,
        )

        config = AIProviderConfig.objects.filter(
            organization=membership.organization
        ).first()

        if not config:
            return Response({
                "configured": False,
            })

        return Response({
            "configured": True,
            "provider": config.provider,
            "model_name": config.model_name,
            "api_base": config.api_base,
            "is_enabled": config.is_enabled,
            "has_api_key": bool(config.encrypted_api_key),
        })

    def put(self, request, organization_id):
        membership = self.get_membership(
            request,
            organization_id,
        )

        if membership.role not in [
            Membership.Role.OWNER,
            Membership.Role.ADMIN,
        ]:
            return Response(
                {"detail": "Only organization owners and admins can configure AI."},
                status=status.HTTP_403_FORBIDDEN,
            )

        provider = request.data.get("provider")
        model_name = request.data.get("model_name")
        api_key = request.data.get("api_key")
        api_base = request.data.get("api_base", "")
        is_enabled = request.data.get("is_enabled", True)

        if not provider or not model_name:
            return Response(
                {"detail": "Provider and model_name are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(is_enabled, bool):
            return Response(
                {"detail": "is_enabled must be a boolean."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if api_base is None:
            api_base = ""

        if not isinstance(api_base, str):
            return Response(
                {"detail": "api_base must be a string."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        config, created = AIProviderConfig.objects.get_or_create(
            organization=membership.organization,
            defaults={
                "provider": provider,
                "model_name": model_name,
                "encrypted_api_key": "",
            },
        )

        config.provider = provider
        config.model_name = model_name
        config.api_base = api_base
        config.is_enabled = is_enabled

        if api_key is not None:
            if not isinstance(api_key, str) or not api_key.strip():
                return Response(
                    {"detail": "api_key must be a non-empty string."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                config.encrypted_api_key = encrypt_api_key(api_key.strip())
            except Exception:
                logger.exception("AI API key encryption failed.")
                return Response(
                    {"detail": "Unable to securely store API key."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        elif created:
            return Response(
                {"detail": "An API key is required for initial configuration."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        config.save()

        return Response({
            "configured": True,
            "provider": config.provider,
            "model_name": config.model_name,
            "api_base": config.api_base,
            "is_enabled": config.is_enabled,
            "has_api_key": bool(config.encrypted_api_key),
        })


class AIProviderTestView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, organization_id):
        membership = get_object_or_404(
            Membership,
            user=request.user,
            organization_id=organization_id,
        )

        if membership.role not in [
            Membership.Role.OWNER,
            Membership.Role.ADMIN,
        ]:
            return Response(
                {"detail": "Only organization owners and admins can test AI configuration."},
                status=status.HTTP_403_FORBIDDEN,
            )

        config = get_object_or_404(
            AIProviderConfig,
            organization=membership.organization,
        )

        if not config.is_enabled or not config.encrypted_api_key:
            return Response(
                {"detail": "AI provider is disabled or has no API key."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            api_key = decrypt_api_key(config.encrypted_api_key)

            content = generate_completion(
                model=config.model_name,
                api_key=api_key,
                api_base=config.api_base or None,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Reply with exactly this text: "
                            "RuntimeRCA connection successful"
                        ),
                    }
                ],
                timeout=30,
            )

            return Response({
                "success": True,
                "provider": config.provider,
                "model": config.model_name,
                "response": content[:500],
            })

        except Exception:
            logger.exception("AI provider connection test failed.")

            return Response(
                {
                    "success": False,
                    "detail": "AI provider connection failed. Check provider, model and credentials.",
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )
class OrganizationListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        memberships = Membership.objects.filter(
            user=request.user
        ).select_related("organization")

        return Response({
            "results": [
                {
                    "id": membership.organization.id,
                    "name": membership.organization.name,
                    "slug": membership.organization.slug,
                    "role": membership.role,
                }
                for membership in memberships
            ]
        })