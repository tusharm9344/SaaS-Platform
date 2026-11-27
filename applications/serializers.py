from rest_framework import serializers

from applications.models import DiscoveredContainer, Service


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
