from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('regulacao', '0013_rename_regulacao_n_user_l_a9e08f_idx_regulacao_n_user_id_5c62bf_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='LocalAtendimento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=200, verbose_name='Nome do Local')),
                ('tipo', models.CharField(choices=[('ambulatorio', 'Ambulatório'), ('centro_imagem', 'Centro de Imagem'), ('laboratorio', 'Laboratório'), ('clinica', 'Clínica'), ('hospital', 'Hospital'), ('outro', 'Outro')], default='outro', max_length=20, verbose_name='Tipo')),
                ('endereco', models.TextField(blank=True, max_length=300, verbose_name='Endereço')),
                ('telefone', models.CharField(blank=True, max_length=30, verbose_name='Telefone')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Local de Atendimento',
                'verbose_name_plural': 'Locais de Atendimento',
                'ordering': ['nome'],
            },
        ),
    ]
