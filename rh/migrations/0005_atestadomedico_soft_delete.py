from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rh', '0004_atestadomedico'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='atestadomedico',
            name='ativo',
            field=models.BooleanField(default=True, verbose_name='Ativo'),
        ),
        migrations.AddField(
            model_name='atestadomedico',
            name='removido_em',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Removido em'),
        ),
        migrations.AddField(
            model_name='atestadomedico',
            name='removido_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='atestados_removidos', to=settings.AUTH_USER_MODEL, verbose_name='Removido por'),
        ),
    ]
