from django.db import migrations


def forwards(apps, schema_editor):
    Viagem = apps.get_model('viagens', 'Viagem')
    Motorista = apps.get_model('motorista', 'Motorista')
    for v in Viagem.objects.all().iterator():
        nome = (v.motorista or '').strip()
        if not nome or nome.lower() in ['não informado', 'nao informado']:
            continue
        m = Motorista.objects.filter(nome_completo__iexact=nome).first()
        if m:
            v.motorista_ref_id = m.id
            v.save(update_fields=['motorista_ref_id'])


def backwards(apps, schema_editor):
    # No-op: manter dados
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('viagens', '0007_viagem_add_motorista_ref'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
