from rest_framework import serializers

from incidents.models import Incident
from ingestion.models import ErrorEvent
from investigations.models import Investigation


class IncidentSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(
        source="service.name",
        read_only=True,
        default=None,
    )

    environment = serializers.CharField(
        source="service.environment",
        read_only=True,
        default=None,
    )

    class Meta:
        model = Incident
        fields = [
            "id",
            "application",
            "service",
            "service_name",
            "environment",
            "fingerprint",
            "title",
            "status",
            "occurrence_count",
            "first_seen",
            "last_seen",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ErrorEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErrorEvent
        fields = [
            "id",
            "message",
            "exception_type",
            "stack_trace",
            "severity",
            "environment",
            "occurred_at",
            "received_at",
        ]
        read_only_fields = fields


class InvestigationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investigation
        fields = [
            "id",
            "incident",
            "status",
            "summary",
            "hypotheses",
            "evidence",
            "recommended_actions",
            "created_at",
            "completed_at",
        ]
        read_only_fields = fields


class IncidentDetailSerializer(IncidentSerializer):
    recent_events = serializers.SerializerMethodField()
    investigation = InvestigationSerializer(read_only=True)

    class Meta(IncidentSerializer.Meta):
        fields = IncidentSerializer.Meta.fields + [
            "recent_events",
            "investigation",
        ]

    def get_recent_events(self, obj):
        events = ErrorEvent.objects.filter(
            incident=obj
        ).order_by("-received_at")[:20]

        return ErrorEventSerializer(events, many=True).data