from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupAccess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('can_pacientes', models.BooleanField(default=False, verbose_name='Pacientes')),
                ('can_viagens', models.BooleanField(default=False, verbose_name='Viagens')),
                ('can_tfd', models.BooleanField(default=False, verbose_name='TFD')),
                ('can_regulacao', models.BooleanField(default=False, verbose_name='Regulação')),
                ('can_users_admin', models.BooleanField(default=False, verbose_name='Administração de Usuários/Grupos')),
                ('group', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='access', to='auth.group')),
            ],
            options={
                'verbose_name': 'Acesso do Grupo',
                'verbose_name_plural': 'Acessos dos Grupos',
            },
        ),
    ]
