from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('motorista', '0001_initial'),
        ('viagens', '0006_remove_viagem_tipo_transporte_viagem_acompanhante_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='viagem',
            name='motorista_ref',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='viagens_agendadas', to='motorista.motorista'),
        ),
    ]
