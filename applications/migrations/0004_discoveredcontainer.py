import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0003_service"),
    ]

    operations = [
        migrations.CreateModel(
            name="DiscoveredContainer",
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
                ("container_id", models.CharField(max_length=128)),
                ("name", models.CharField(max_length=255)),
                ("image", models.CharField(max_length=500)),
                ("status", models.CharField(max_length=50)),
                ("labels", models.JSONField(blank=True, default=dict)),
                ("is_monitored", models.BooleanField(default=True)),
                ("first_seen", models.DateTimeField(auto_now_add=True)),
                ("last_seen", models.DateTimeField(auto_now=True)),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="discovered_containers",
                        to="applications.application",
                    ),
                ),
                (
                    "service",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="containers",
                        to="applications.service",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["application", "status"],
                        name="container_app_status_idx",
                    )
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("application", "container_id"),
                        name="unique_container_per_application",
                    )
                ],
            },
        ),
    ]
