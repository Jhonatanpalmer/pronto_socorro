from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('viagens', '0008_populate_motorista_ref'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='viagem',
            name='motorista',
        ),
        migrations.RenameField(
            model_name='viagem',
            old_name='motorista_ref',
            new_name='motorista',
        ),
    ]
