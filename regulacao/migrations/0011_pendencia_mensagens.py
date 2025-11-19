from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('regulacao', '0010_merge_0003_pendencia_fields_0009_merge_20250925_1937'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PendenciaMensagemExame',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lado', models.CharField(choices=[('ubs', 'UBS'), ('regulacao', 'Regulação')], max_length=20)),
                ('tipo', models.CharField(choices=[('mensagem', 'Mensagem'), ('abertura', 'Abertura da Pendência')], default='mensagem', max_length=20)),
                ('texto', models.TextField()),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('autor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('exame', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pendencia_mensagens', to='regulacao.regulacaoexame')),
            ],
            options={'ordering': ['criado_em']},
        ),
        migrations.AddIndex(
            model_name='pendenciamensagemexame',
            index=models.Index(fields=['exame', 'criado_em'], name='reg_exame_msg_idx'),
        ),
        migrations.CreateModel(
            name='PendenciaMensagemConsulta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lado', models.CharField(choices=[('ubs', 'UBS'), ('regulacao', 'Regulação')], max_length=20)),
                ('tipo', models.CharField(choices=[('mensagem', 'Mensagem'), ('abertura', 'Abertura da Pendência')], default='mensagem', max_length=20)),
                ('texto', models.TextField()),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('autor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('consulta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pendencia_mensagens', to='regulacao.regulacaoconsulta')),
            ],
            options={'ordering': ['criado_em']},
        ),
        migrations.AddIndex(
            model_name='pendenciamensagemconsulta',
            index=models.Index(fields=['consulta', 'criado_em'], name='reg_cons_msg_idx'),
        ),
    ]
