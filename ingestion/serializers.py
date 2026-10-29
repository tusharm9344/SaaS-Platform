from rest_framework import serializers

from ingestion.models import ErrorEvent


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
        ]
        read_only_fields = ["id"]

    def validate_message(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Error message cannot be empty."
            )

        if len(value) > 20000:
            raise serializers.ValidationError(
                "Error message is too long."
            )

        return value

    def validate_stack_trace(self, value):
        if len(value) > 100000:
            raise serializers.ValidationError(
                "Stack trace is too long."
            )

        return value

    def validate_exception_type(self, value):
        if len(value) > 255:
            raise serializers.ValidationError(
                "Exception type is too long."
            )

        return value