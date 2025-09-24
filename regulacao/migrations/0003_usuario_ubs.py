from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('regulacao', '0006_noop_protocolo_logic_change'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UsuarioUBS',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ubs', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usuarios', to='regulacao.ubs')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='perfil_ubs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Usuário da UBS',
                'verbose_name_plural': 'Usuários das UBS',
            },
        ),
    ]
