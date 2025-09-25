from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('regulacao', '0007_usuario_ubs'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='regulacaoconsulta',
            name='resultado_atendimento',
            field=models.CharField(choices=[('pendente', 'Pendente'), ('compareceu', 'Compareceu'), ('faltou', 'Faltou')], db_index=True, default='pendente', max_length=12, verbose_name='Resultado do Atendimento'),
        ),
        migrations.AddField(
            model_name='regulacaoconsulta',
            name='resultado_em',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Resultado registrado em'),
        ),
        migrations.AddField(
            model_name='regulacaoconsulta',
            name='resultado_observacao',
            field=models.TextField(blank=True, verbose_name='Observação do Resultado'),
        ),
        migrations.AddField(
            model_name='regulacaoconsulta',
            name='resultado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Resultado registrado por'),
        ),
        migrations.AddField(
            model_name='regulacaoexame',
            name='resultado_atendimento',
            field=models.CharField(choices=[('pendente', 'Pendente'), ('compareceu', 'Compareceu'), ('faltou', 'Faltou')], db_index=True, default='pendente', max_length=12, verbose_name='Resultado do Atendimento'),
        ),
        migrations.AddField(
            model_name='regulacaoexame',
            name='resultado_em',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Resultado registrado em'),
        ),
        migrations.AddField(
            model_name='regulacaoexame',
            name='resultado_observacao',
            field=models.TextField(blank=True, verbose_name='Observação do Resultado'),
        ),
        migrations.AddField(
            model_name='regulacaoexame',
            name='resultado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Resultado registrado por'),
        ),
    ]
