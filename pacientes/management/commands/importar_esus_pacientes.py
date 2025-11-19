from django.core.management.base import BaseCommand, CommandError
from pacientes.models import Paciente
from pacientes.services import buscar_paciente_esus, atualizar_paciente_com_esus


class Command(BaseCommand):
    help = 'Importa/atualiza pacientes a partir do banco e-SUS por CPF ou CNS.'

    def add_arguments(self, parser):
        parser.add_argument('--cpf', help='CPF do paciente para importar (somente dígitos).')
        parser.add_argument('--cns', help='CNS do paciente para importar.')
        parser.add_argument('--sobrescrever', action='store_true', help='Sobrescreve campos existentes no cadastro local.')

    def handle(self, *args, **options):
        cpf = options.get('cpf')
        cns = options.get('cns')
        sobrescrever = bool(options.get('sobrescrever'))
        if not cpf and not cns:
            raise CommandError('Informe --cpf ou --cns')

        dados = buscar_paciente_esus(cpf=cpf, cns=cns)
        if not dados:
            self.stdout.write(self.style.WARNING('Não encontrado no e-SUS.'))
            return

        # Tentar localizar paciente local por CPF, depois por CNS e, por fim, por nome+data
        pac = None
        if dados.get('cpf'):
            pac = Paciente.objects.filter(cpf=''.join(filter(str.isdigit, dados['cpf']))).first()
        if not pac and dados.get('cns'):
            pac = Paciente.objects.filter(cns=dados['cns']).first()
        if not pac:
            # fallback por nome+data (pode criar duplicatas em homônimos)
            dn = dados.get('data_nascimento')
            pac = Paciente.objects.filter(nome=dados['nome'], data_nascimento=dn).first()
        if not pac:
            pac = Paciente(nome=dados['nome'], data_nascimento=dados['data_nascimento'])
            pac.save()

        pac = atualizar_paciente_com_esus(pac, dados, sobrescrever=sobrescrever)
        self.stdout.write(self.style.SUCCESS(f'Paciente atualizado: {pac.id} - {pac.nome}'))
