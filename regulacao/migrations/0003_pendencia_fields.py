from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('regulacao', '0002_tipoexame_codigo_tipoexame_valor_and_more'),
    ]

    operations = [
        # RegulacaoExame fields
        migrations.AddField(
            model_name='regulacaoexame',
            name='pendencia_motivo',
            field=models.TextField(blank=True, help_text='Descreva o que falta ou o que precisa ser corrigido pela UBS', verbose_name='Motivo da Pendência'),
        ),
        migrations.AddField(
            model_name='regulacaoexame',
            name='pendencia_aberta_em',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Pendência aberta em'),
        ),
        migrations.AddField(
            model_name='regulacaoexame',
            name='pendencia_aberta_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='auth.user', verbose_name='Pendência aberta por'),
        ),
        migrations.AddField(
            model_name='regulacaoexame',
            name='pendencia_resposta',
            field=models.TextField(blank=True, verbose_name='Resposta da UBS'),
        ),
        migrations.AddField(
            model_name='regulacaoexame',
            name='pendencia_respondida_em',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Pendência respondida em'),
        ),
        migrations.AddField(
            model_name='regulacaoexame',
            name='pendencia_respondida_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='auth.user', verbose_name='Resposta registrada por'),
        ),
        migrations.AddField(
            model_name='regulacaoexame',
            name='pendencia_resolvida_em',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Pendência resolvida em'),
        ),
        migrations.AddField(
            model_name='regulacaoexame',
            name='pendencia_resolvida_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='auth.user', verbose_name='Pendência resolvida por'),
        ),

        # RegulacaoConsulta fields
        migrations.AddField(
            model_name='regulacaoconsulta',
            name='pendencia_motivo',
            field=models.TextField(blank=True, help_text='Descreva o que falta ou o que precisa ser corrigido pela UBS', verbose_name='Motivo da Pendência'),
        ),
        migrations.AddField(
            model_name='regulacaoconsulta',
            name='pendencia_aberta_em',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Pendência aberta em'),
        ),
        migrations.AddField(
            model_name='regulacaoconsulta',
            name='pendencia_aberta_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='auth.user', verbose_name='Pendência aberta por'),
        ),
        migrations.AddField(
            model_name='regulacaoconsulta',
            name='pendencia_resposta',
            field=models.TextField(blank=True, verbose_name='Resposta da UBS'),
        ),
        migrations.AddField(
            model_name='regulacaoconsulta',
            name='pendencia_respondida_em',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Pendência respondida em'),
        ),
        migrations.AddField(
            model_name='regulacaoconsulta',
            name='pendencia_respondida_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='auth.user', verbose_name='Resposta registrada por'),
        ),
        migrations.AddField(
            model_name='regulacaoconsulta',
            name='pendencia_resolvida_em',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Pendência resolvida em'),
        ),
        migrations.AddField(
            model_name='regulacaoconsulta',
            name='pendencia_resolvida_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='auth.user', verbose_name='Pendência resolvida por'),
        ),
    ]
