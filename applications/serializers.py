from rest_framework import serializers

from applications.models import (
    Application,
    ApplicationAPIKey,
    DiscoveredContainer,
    Service,
)


class ApplicationSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
    )
    services_count = serializers.SerializerMethodField()
    active_api_keys_count = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            "id",
            "organization",
            "organization_name",
            "name",
            "slug",
            "description",
            "is_active",
            "services_count",
            "active_api_keys_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization",
            "organization_name",
            "services_count",
            "active_api_keys_count",
            "created_at",
            "updated_at",
        ]
        validators = []

    def get_services_count(self, obj):
        return obj.services.count()

    def get_active_api_keys_count(self, obj):
        return obj.api_keys.filter(
            is_active=True,
            revoked_at__isnull=True,
        ).count()


class ApplicationAPIKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationAPIKey
        fields = [
            "id",
            "name",
            "key_prefix",
            "is_active",
            "created_at",
            "revoked_at",
        ]
        read_only_fields = fields


class ServiceSerializer(serializers.ModelSerializer):
    application_name = serializers.CharField(
        source="application.name",
        read_only=True,
    )

    class Meta:
        model = Service
        fields = [
            "id",
            "application",
            "application_name",
            "name",
            "environment",
            "is_active",
            "first_seen",
            "last_seen",
        ]
        read_only_fields = [
            "id",
            "application",
            "application_name",
            "name",
            "environment",
            "first_seen",
            "last_seen",
        ]


class ContainerDiscoverySerializer(serializers.Serializer):
    container_id = serializers.CharField(max_length=128)
    name = serializers.CharField(max_length=255)
    image = serializers.CharField(max_length=500)
    status = serializers.CharField(max_length=50)

    health_status = serializers.CharField(
        max_length=20,
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    service_name = serializers.CharField(max_length=200)

    environment = serializers.CharField(
        max_length=50,
        default="production",
    )

    cpu_percent = serializers.FloatField(required=False, allow_null=True)
    memory_usage = serializers.IntegerField(required=False, allow_null=True)
    memory_limit = serializers.IntegerField(required=False, allow_null=True)
    memory_percent = serializers.FloatField(required=False, allow_null=True)

    labels = serializers.DictField(
        required=False,
        default=dict,
    )


class DiscoveredContainerSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(
        source="service.name",
        read_only=True,
    )

    environment = serializers.CharField(
        source="service.environment",
        read_only=True,
    )

    memory_usage_mb = serializers.SerializerMethodField()
    memory_limit_mb = serializers.SerializerMethodField()

    class Meta:
        model = DiscoveredContainer
        fields = [
            "id",
            "container_id",
            "name",
            "image",
            "status",
            "health_status",
            "service",
            "service_name",
            "environment",
            "is_monitored",
            "cpu_percent",
            "memory_usage",
            "memory_usage_mb",
            "memory_limit",
            "memory_limit_mb",
            "memory_percent",
            "metrics_updated_at",
            "first_seen",
            "last_seen",
        ]

    def get_memory_usage_mb(self, obj):
        if obj.memory_usage is None:
            return None
        return round(obj.memory_usage / (1024 * 1024), 2)

    def get_memory_limit_mb(self, obj):
        if obj.memory_limit is None:
            return None
        return round(obj.memory_limit / (1024 * 1024), 2)