from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ("motorista", "0001_initial"),
        ("veiculos", "0003_veiculo_combustivel"),
    ]

    operations = [
        migrations.AlterField(
            model_name="abastecimento",
            name="motorista",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="abastecimentos",
                to="motorista.motorista",
            ),
        ),
    ]
