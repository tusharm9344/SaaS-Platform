import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0004_discoveredcontainer"),
    ]

    operations = [
        migrations.CreateModel(
            name="DiscoveryAgent",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("agent_id", models.CharField(max_length=64)),
                ("hostname", models.CharField(max_length=255)),
                (
                    "last_heartbeat",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="discovery_agents",
                        to="applications.application",
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("application", "agent_id"),
                        name="unique_discovery_agent_per_application",
                    )
                ],
            },
        ),
        migrations.AddField(
            model_name="discoveredcontainer",
            name="agent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="containers",
                to="applications.discoveryagent",
            ),
        ),
    ]
