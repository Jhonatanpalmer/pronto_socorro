from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('regulacao', '0002_tipoexame_codigo_tipoexame_valor_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='regulacaoexame',
            name='numero_pedido',
            field=models.CharField(
                verbose_name='Número do Pedido',
                max_length=50,
                blank=True,
                help_text='Identificador comum para agrupar vários exames no mesmo pedido',
                db_index=True,
            ),
        ),
    ]
