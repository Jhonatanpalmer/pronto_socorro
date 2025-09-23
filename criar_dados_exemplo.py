import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'secretaria_it.settings')
django.setup()

from regulacao.models import UBS, MedicoSolicitante, TipoExame

# Criar UBS
ubs_data = [
    {
        'nome': 'UBS Centro',
        'endereco': 'Rua Principal, 123 - Centro',
        'responsavel': 'Dr. João Silva',
        'telefone': '(34) 3271-1234',
        'email': 'ubs.centro@iturama.mg.gov.br',
        'ativa': True
    },
    {
        'nome': 'UBS Vila Nova',
        'endereco': 'Av. Brasil, 456 - Vila Nova',
        'responsavel': 'Dra. Maria Santos',
        'telefone': '(34) 3271-2345',
        'email': 'ubs.vilanova@iturama.mg.gov.br',
        'ativa': True
    },
    {
        'nome': 'UBS São José',
        'endereco': 'Rua São José, 789 - São José',
        'responsavel': 'Dr. Pedro Costa',
        'telefone': '(34) 3271-3456',
        'email': 'ubs.saojose@iturama.mg.gov.br',
        'ativa': True
    }
]

print("Criando UBS...")
for ubs_info in ubs_data:
    ubs, created = UBS.objects.get_or_create(
        nome=ubs_info['nome'],
        defaults=ubs_info
    )
    if created:
        print(f"✓ UBS '{ubs.nome}' criada com sucesso!")
    else:
        print(f"• UBS '{ubs.nome}' já existe.")

print(f"\nTotal de UBS cadastradas: {UBS.objects.count()}")

# Criar Médicos
print("\nCriando Médicos...")
ubs_centro = UBS.objects.get(nome='UBS Centro')
ubs_vila_nova = UBS.objects.get(nome='UBS Vila Nova')
ubs_sao_jose = UBS.objects.get(nome='UBS São José')

medicos_data = [
    {
        'nome': 'Dr. Carlos Ferreira',
        'crm': 'CRM-MG 12345',
        'especialidade': 'Clínico Geral',
        'ubs_padrao': ubs_centro,
        'telefone': '(34) 99999-1111',
        'email': 'carlos.ferreira@iturama.mg.gov.br',
        'ativo': True
    },
    {
        'nome': 'Dra. Ana Paula Lima',
        'crm': 'CRM-MG 23456',
        'especialidade': 'Ginecologia',
        'ubs_padrao': ubs_vila_nova,
        'telefone': '(34) 99999-2222',
        'email': 'ana.lima@iturama.mg.gov.br',
        'ativo': True
    },
    {
        'nome': 'Dr. Roberto Oliveira',
        'crm': 'CRM-MG 34567',
        'especialidade': 'Pediatria',
        'ubs_padrao': ubs_sao_jose,
        'telefone': '(34) 99999-3333',
        'email': 'roberto.oliveira@iturama.mg.gov.br',
        'ativo': True
    }
]

for medico_info in medicos_data:
    medico, created = MedicoSolicitante.objects.get_or_create(
        crm=medico_info['crm'],
        defaults=medico_info
    )
    if created:
        print(f"✓ Médico '{medico.nome}' criado com sucesso!")
    else:
        print(f"• Médico '{medico.nome}' já existe.")

print(f"Total de Médicos cadastrados: {MedicoSolicitante.objects.count()}")

# Criar Tipos de Exames
print("\nCriando Tipos de Exames...")
tipos_exames_data = [
    {
        'codigo': 'HEM001',
        'nome': 'Hemograma Completo',
        'descricao': 'Exame de sangue completo para avaliar células sanguíneas',
        'valor': 25.00,
        'ativo': True
    },
    {
        'codigo': 'URO001',
        'nome': 'Exame de Urina (EAS)',
        'descricao': 'Exame de urina tipo I para análise físico-química',
        'valor': 15.00,
        'ativo': True
    },
    {
        'codigo': 'RAD001',
        'nome': 'Raio-X de Tórax',
        'descricao': 'Radiografia do tórax PA e perfil',
        'valor': 45.00,
        'ativo': True
    },
    {
        'codigo': 'ECG001',
        'nome': 'Eletrocardiograma',
        'descricao': 'ECG de repouso com 12 derivações',
        'valor': 30.00,
        'ativo': True
    },
    {
        'codigo': 'GLI001',
        'nome': 'Glicemia de Jejum',
        'descricao': 'Dosagem de glicose em jejum',
        'valor': 12.00,
        'ativo': True
    }
]

for tipo_info in tipos_exames_data:
    tipo, created = TipoExame.objects.get_or_create(
        codigo=tipo_info['codigo'],
        defaults=tipo_info
    )
    if created:
        print(f"✓ Tipo de Exame '{tipo.nome}' criado com sucesso!")
    else:
        print(f"• Tipo de Exame '{tipo.nome}' já existe.")

print(f"Total de Tipos de Exames cadastrados: {TipoExame.objects.count()}")
print("\n🎉 Dados de exemplo criados com sucesso!")