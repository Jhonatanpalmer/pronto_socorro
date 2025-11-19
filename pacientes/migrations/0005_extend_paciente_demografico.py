from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pacientes', '0004_alter_paciente_cns_alter_paciente_nome'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paciente',
            name='endereco',
            field=models.TextField(max_length=300),
        ),
        migrations.AddField(
            model_name='paciente',
            name='logradouro',
            field=models.CharField(blank=True, help_text='Rua/Avenida/Travessa', max_length=120),
        ),
        migrations.AddField(
            model_name='paciente',
            name='numero',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='paciente',
            name='bairro',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name='paciente',
            name='cep',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='paciente',
            name='nome_mae',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='paciente',
            name='nome_pai',
            field=models.CharField(blank=True, max_length=150),
        ),
    ]
