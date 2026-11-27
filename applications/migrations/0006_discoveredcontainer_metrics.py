from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0005_discoveryagent_container_agent"),
    ]

    operations = [
        migrations.AddField(
            model_name="discoveredcontainer",
            name="cpu_percent",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="discoveredcontainer",
            name="memory_usage",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="discoveredcontainer",
            name="memory_limit",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="discoveredcontainer",
            name="memory_percent",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="discoveredcontainer",
            name="metrics_updated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
