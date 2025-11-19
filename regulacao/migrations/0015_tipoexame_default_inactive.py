from django.db import migrations


def set_all_tipoexame_inactive(apps, schema_editor):
    TipoExame = apps.get_model('regulacao', 'TipoExame')
    TipoExame.objects.update(ativo=False)


def reverse_noop(apps, schema_editor):
    # Não reativa automaticamente; reversão não altera dados
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('regulacao', '0014_localatendimento'),
    ]

    operations = [
        migrations.RunPython(set_all_tipoexame_inactive, reverse_noop),
    ]
