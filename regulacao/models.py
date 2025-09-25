from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UBS(models.Model):
    """Unidade Básica de Saúde - cadastro das UBS solicitantes"""
    nome = models.CharField('Nome da UBS', max_length=200)
    endereco = models.TextField('Endereço', max_length=300, blank=True)
    telefone = models.CharField('Telefone', max_length=30, blank=True)
    email = models.EmailField('E-mail', blank=True)
    responsavel = models.CharField('Responsável', max_length=150, blank=True)
    ativa = models.BooleanField('Ativa', default=True)
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'UBS'
        verbose_name_plural = 'UBS'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class UsuarioUBS(models.Model):
    """Associação 1-para-1 de usuário a uma UBS específica."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_ubs')
    ubs = models.ForeignKey(UBS, on_delete=models.CASCADE, related_name='usuarios')

    class Meta:
        verbose_name = 'Usuário da UBS'
        verbose_name_plural = 'Usuários das UBS'
        unique_together = ('user',)

    def __str__(self):  # pragma: no cover
        return f"{self.user.username} @ {self.ubs.nome}"


class MedicoSolicitante(models.Model):
    """Médicos que podem solicitar exames"""
    nome = models.CharField('Nome do Médico', max_length=150)
    crm = models.CharField('CRM', max_length=20, unique=True)
    especialidade = models.CharField('Especialidade', max_length=100, blank=True)
    telefone = models.CharField('Telefone', max_length=30, blank=True)
    email = models.EmailField('E-mail', blank=True)
    ubs_padrao = models.ForeignKey(UBS, on_delete=models.SET_NULL, null=True, blank=True, 
                                   verbose_name='UBS Padrão')
    ativo = models.BooleanField('Ativo', default=True)
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Médico Solicitante'
        verbose_name_plural = 'Médicos Solicitantes'
        ordering = ['nome']
    
    def __str__(self):
        return f"Dr(a). {self.nome} - CRM: {self.crm}"


class TipoExame(models.Model):
    """Tipos de exames disponíveis"""
    nome = models.CharField('Nome do Exame', max_length=200)
    codigo = models.CharField('Código', max_length=20, blank=True)
    descricao = models.TextField('Descrição', blank=True)
    codigo_sus = models.CharField('Código SUS', max_length=20, blank=True)
    valor = models.DecimalField('Valor (R$)', max_digits=10, decimal_places=2, null=True, blank=True)
    ativo = models.BooleanField('Ativo', default=True)
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Tipo de Exame'
        verbose_name_plural = 'Tipos de Exames'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class RegulacaoExame(models.Model):
    """Solicitação e regulação de exames"""
    
    STATUS_CHOICES = [
        ('fila', 'Fila de Espera'),
        ('pendente', 'Pendente'),
        ('autorizado', 'Autorizado'),
        ('negado', 'Negado'),
        ('cancelado', 'Cancelado'),
    ]
    
    PRIORIDADE_CHOICES = [
        ('normal', 'Normal'),
        ('media', 'Média'),
        ('alta', 'Alta'),
    ]
    
    # Dados do paciente
    paciente = models.ForeignKey('pacientes.Paciente', on_delete=models.CASCADE,
                                verbose_name='Paciente')
    
    # Dados da solicitação
    ubs_solicitante = models.ForeignKey(UBS, on_delete=models.CASCADE,
                                       verbose_name='UBS Solicitante')
    medico_solicitante = models.ForeignKey(MedicoSolicitante, on_delete=models.CASCADE,
                                          verbose_name='Médico Solicitante')
    tipo_exame = models.ForeignKey(TipoExame, on_delete=models.CASCADE,
                                  verbose_name='Tipo de Exame')
    
    # Detalhes da solicitação
    justificativa = models.TextField('Justificativa Clínica', 
                                    help_text='Motivo/indicação clínica para o exame')
    prioridade = models.CharField('Prioridade', max_length=20, 
                                 choices=PRIORIDADE_CHOICES, default='normal')
    observacoes_solicitacao = models.TextField('Observações da Solicitação', blank=True)
    
    # Status e regulação
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, 
                             default='fila')
    data_solicitacao = models.DateTimeField('Data da Solicitação', auto_now_add=True)
    data_regulacao = models.DateTimeField('Data da Regulação', null=True, blank=True)
    
    # Dados da regulação (quando autorizado/negado)
    regulador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name='Regulador', 
                                 help_text='Usuário que fez a regulação')
    motivo_decisao = models.TextField('Motivo da Decisão', blank=True,
                                     help_text='Motivo da autorização ou negação')
    
    # Dados quando autorizado
    local_realizacao = models.CharField('Local de Realização', max_length=200, blank=True)
    data_agendada = models.DateField('Data Agendada', null=True, blank=True)
    hora_agendada = models.TimeField('Hora Agendada', null=True, blank=True)
    medico_atendente = models.ForeignKey(
        MedicoSolicitante,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Médico Atendente',
        related_name='atendimentos_exames',
    )
    observacoes_regulacao = models.TextField('Observações da Regulação', blank=True)
    
    # Controle
    numero_pedido = models.CharField('Número do Pedido', max_length=50, blank=True, db_index=True,
                                     help_text='Identificador comum para agrupar vários exames no mesmo pedido')
    numero_protocolo = models.CharField('Número do Protocolo', max_length=50, unique=True,
                                       blank=True, help_text='Gerado automaticamente')
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    # Resultado do atendimento (marcado após a data agendada)
    RESULTADO_CHOICES = [
        ('pendente', 'Pendente'),
        ('compareceu', 'Compareceu'),
        ('faltou', 'Faltou'),
    ]
    resultado_atendimento = models.CharField('Resultado do Atendimento', max_length=12, choices=RESULTADO_CHOICES, default='pendente', db_index=True)
    resultado_observacao = models.TextField('Observação do Resultado', blank=True)
    resultado_em = models.DateTimeField('Resultado registrado em', null=True, blank=True)
    resultado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name='Resultado registrado por')
    
    class Meta:
        verbose_name = 'Regulação de Exame'
        verbose_name_plural = 'Regulações de Exames'
        ordering = ['-data_solicitacao']
    
    def __str__(self):
        return f"Protocolo {self.numero_protocolo} - {self.paciente.nome} - {self.tipo_exame.nome}"
    
    def save(self, *args, **kwargs):
        # Gerar número de protocolo no padrão: exa + ddmmyyyy + sufixo incremental diário
        if not self.numero_protocolo:
            base = f"exa{timezone.localdate().strftime('%d%m%Y')}"
            # Garante unicidade adicionando um sufixo incremental por dia
            seq = 1
            numero = f"{base}-{seq:04d}"
            while type(self).objects.filter(numero_protocolo=numero).exists():
                seq += 1
                numero = f"{base}-{seq:04d}"
            self.numero_protocolo = numero
        super().save(*args, **kwargs)
    
    def get_status_badge_class(self):
        """Retorna classe CSS para badge de status"""
        classes = {
            'fila': 'bg-info text-dark',
            'pendente': 'bg-warning text-dark',
            'autorizado': 'bg-success',
            'negado': 'bg-danger',
            'cancelado': 'bg-secondary',
        }
        return classes.get(self.status, 'bg-secondary')
    
    def get_prioridade_badge_class(self):
        """Retorna classe CSS para badge de prioridade"""
        classes = {
            'normal': 'bg-primary',
            'urgente': 'bg-warning text-dark',
            'emergencia': 'bg-danger',
        }
        return classes.get(self.prioridade, 'bg-primary')

    def get_resultado_badge_class(self):
        classes = {
            'pendente': 'bg-secondary',
            'compareceu': 'bg-success',
            'faltou': 'bg-danger',
        }
        return classes.get(self.resultado_atendimento or 'pendente', 'bg-secondary')


class Especialidade(models.Model):
    """Especialidades médicas para consultas (Cardiologia, Ortopedia, etc.)"""
    nome = models.CharField('Nome da Especialidade', max_length=150, unique=True)
    descricao = models.TextField('Descrição', blank=True)
    ativa = models.BooleanField('Ativa', default=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Especialidade'
        verbose_name_plural = 'Especialidades'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class RegulacaoConsulta(models.Model):
    """Solicitação e regulação de consultas por especialidade"""

    STATUS_CHOICES = [
        ('fila', 'Fila de Espera'),
        ('pendente', 'Pendente'),
        ('autorizado', 'Autorizado'),
        ('negado', 'Negado'),
        ('cancelado', 'Cancelado'),
    ]

    PRIORIDADE_CHOICES = [
        ('normal', 'Normal'),
        ('media', 'Média'),
        ('alta', 'Alta'),
    ]

    # Dados do paciente
    paciente = models.ForeignKey('pacientes.Paciente', on_delete=models.CASCADE,
                                 verbose_name='Paciente')

    # Dados da solicitação
    ubs_solicitante = models.ForeignKey(UBS, on_delete=models.CASCADE,
                                        verbose_name='UBS Solicitante')
    medico_solicitante = models.ForeignKey(MedicoSolicitante, on_delete=models.CASCADE,
                                           verbose_name='Médico Solicitante')
    especialidade = models.ForeignKey(Especialidade, on_delete=models.CASCADE,
                                      verbose_name='Especialidade')

    # Detalhes da solicitação
    justificativa = models.TextField('Justificativa Clínica',
                                     help_text='Motivo/indicação clínica para a consulta')
    prioridade = models.CharField('Prioridade', max_length=20,
                                  choices=PRIORIDADE_CHOICES, default='normal')
    observacoes_solicitacao = models.TextField('Observações da Solicitação', blank=True)

    # Status e regulação
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES,
                              default='fila')
    data_solicitacao = models.DateTimeField('Data da Solicitação', auto_now_add=True)
    data_regulacao = models.DateTimeField('Data da Regulação', null=True, blank=True)

    # Dados da regulação (quando autorizado/negado)
    regulador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  verbose_name='Regulador',
                                  help_text='Usuário que fez a regulação')
    motivo_decisao = models.TextField('Motivo da Decisão', blank=True,
                                      help_text='Motivo da autorização ou negação')

    # Dados quando autorizado
    local_atendimento = models.CharField('Local de Atendimento', max_length=200, blank=True)
    data_agendada = models.DateField('Data Agendada', null=True, blank=True)
    hora_agendada = models.TimeField('Hora Agendada', null=True, blank=True)
    medico_atendente = models.ForeignKey(
        MedicoSolicitante,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Médico Atendente',
        related_name='atendimentos_consultas',
    )
    observacoes_regulacao = models.TextField('Observações da Regulação', blank=True)

    # Controle
    numero_protocolo = models.CharField('Número do Protocolo', max_length=50, unique=True,
                                        blank=True, help_text='Gerado automaticamente')

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    # Resultado do atendimento (marcado após a data agendada)
    RESULTADO_CHOICES = [
        ('pendente', 'Pendente'),
        ('compareceu', 'Compareceu'),
        ('faltou', 'Faltou'),
    ]
    resultado_atendimento = models.CharField('Resultado do Atendimento', max_length=12, choices=RESULTADO_CHOICES, default='pendente', db_index=True)
    resultado_observacao = models.TextField('Observação do Resultado', blank=True)
    resultado_em = models.DateTimeField('Resultado registrado em', null=True, blank=True)
    resultado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name='Resultado registrado por')

    class Meta:
        verbose_name = 'Regulação de Consulta'
        verbose_name_plural = 'Regulações de Consultas'
        ordering = ['-data_solicitacao']

    def __str__(self):
        return f"Protocolo {self.numero_protocolo} - {self.paciente.nome} - {self.especialidade.nome}"

    def save(self, *args, **kwargs):
        # Gerar número de protocolo no padrão: con + ddmmyyyy + sufixo incremental diário
        if not self.numero_protocolo:
            base = f"con{timezone.localdate().strftime('%d%m%Y')}"
            seq = 1
            numero = f"{base}-{seq:04d}"
            while type(self).objects.filter(numero_protocolo=numero).exists():
                seq += 1
                numero = f"{base}-{seq:04d}"
            self.numero_protocolo = numero
        super().save(*args, **kwargs)

    def get_status_badge_class(self):
        classes = {
            'fila': 'bg-info text-dark',
            'pendente': 'bg-warning text-dark',
            'autorizado': 'bg-success',
            'negado': 'bg-danger',
            'cancelado': 'bg-secondary',
        }
        return classes.get(self.status, 'bg-secondary')

    def get_prioridade_badge_class(self):
        classes = {
            'normal': 'bg-primary',
            'urgente': 'bg-warning text-dark',
            'emergencia': 'bg-danger',
        }
        return classes.get(self.prioridade, 'bg-primary')

    def get_resultado_badge_class(self):
        classes = {
            'pendente': 'bg-secondary',
            'compareceu': 'bg-success',
            'faltou': 'bg-danger',
        }
        return classes.get(self.resultado_atendimento or 'pendente', 'bg-secondary')
