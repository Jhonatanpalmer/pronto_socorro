from django.db import migrations


def normalize_vinculo(apps, schema_editor):
    FuncionarioRH = apps.get_model('rh', 'FuncionarioRH')
    # Update any rows with old value 'seletista' to new value 'celetista'
    FuncionarioRH.objects.filter(vinculo='seletista').update(vinculo='celetista')


def reverse_normalize_vinculo(apps, schema_editor):
    FuncionarioRH = apps.get_model('rh', 'FuncionarioRH')
    FuncionarioRH.objects.filter(vinculo='celetista').update(vinculo='seletista')


class Migration(migrations.Migration):

    dependencies = [
        ('rh', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(normalize_vinculo, reverse_normalize_vinculo),
    ]
