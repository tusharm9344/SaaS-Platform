from rest_framework import serializers

from applications.models import Service


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
