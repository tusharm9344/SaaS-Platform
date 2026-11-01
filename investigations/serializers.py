from rest_framework import serializers

from investigations.models import Investigation


class InvestigationSerializer(serializers.ModelSerializer):
    incident_id = serializers.UUIDField(
        source="incident.id",
        read_only=True,
    )

    class Meta:
        model = Investigation
        fields = [
            "id",
            "incident_id",
            "status",
            "summary",
            "hypotheses",
            "evidence",
            "recommended_actions",
            "created_at",
            "completed_at",
        ]
        read_only_fields = fields