from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('regulacao', '0015_tipoexame_default_inactive'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tipoexame',
            name='ativo',
            field=models.BooleanField(default=False, verbose_name='Ativo'),
        ),
    ]
