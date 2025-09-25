from django.db import migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('regulacao', '0007_usuario_ubs'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    # No-op: The resultado_* columns were added by migration 0008 in this database.
    # We keep this migration to satisfy the graph but avoid duplicate field additions.
    operations = []
