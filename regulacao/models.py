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


class LocalAtendimento(models.Model):
    """Locais de atendimento onde exames/consultas podem ser realizados"""

    TIPO_CHOICES = [
        ('ambulatorio', 'Ambulatório'),
        ('centro_imagem', 'Centro de Imagem'),
        ('laboratorio', 'Laboratório'),
        ('clinica', 'Clínica'),
        ('hospital', 'Hospital'),
        ('outro', 'Outro'),
    ]

    nome = models.CharField('Nome do Local', max_length=200)
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES, default='outro')
    endereco = models.TextField('Endereço', max_length=300, blank=True)
    telefone = models.CharField('Telefone', max_length=30, blank=True)
    ativo = models.BooleanField('Ativo', default=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Local de Atendimento'
        verbose_name_plural = 'Locais de Atendimento'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class TipoExame(models.Model):
    """Tipos de exames disponíveis"""
    nome = models.CharField('Nome do Exame', max_length=200)
    codigo = models.CharField('Código', max_length=20, blank=True)
    descricao = models.TextField('Descrição', blank=True)
    codigo_sus = models.CharField('Código SUS', max_length=20, blank=True)
    valor = models.DecimalField('Valor (R$)', max_digits=10, decimal_places=2, null=True, blank=True)
    especialidade = models.ForeignKey(
        'regulacao.Especialidade',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Especialidade responsável',
        help_text='Utilizada para agenda e distribuição de vagas por profissional.'
    )
    # A partir de agora, por padrão tipos de exame nascem inativos e o usuário ativa apenas os que utiliza
    ativo = models.BooleanField('Ativo', default=False)
    
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
        'regulacao.MedicoAmbulatorio',
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
        ('pendente', 'Aguardando'),
        ('compareceu', 'Compareceu'),
        ('faltou', 'Faltou'),
    ]
    resultado_atendimento = models.CharField('Resultado do Atendimento', max_length=12, choices=RESULTADO_CHOICES, default='pendente', db_index=True)
    resultado_observacao = models.TextField('Observação do Resultado', blank=True)
    resultado_em = models.DateTimeField('Resultado registrado em', null=True, blank=True)
    resultado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name='Resultado registrado por')

    # Pendência (interação com UBS quando regulador necessita informação/ação)
    pendencia_motivo = models.TextField('Motivo da Pendência', blank=True,
                                        help_text='Descreva o que falta ou o que precisa ser corrigido pela UBS')
    pendencia_aberta_em = models.DateTimeField('Pendência aberta em', null=True, blank=True)
    pendencia_aberta_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name='Pendência aberta por'
    )
    pendencia_resposta = models.TextField('Resposta da UBS', blank=True)
    pendencia_respondida_em = models.DateTimeField('Pendência respondida em', null=True, blank=True)
    pendencia_respondida_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name='Resposta registrada por'
    )
    pendencia_resolvida_em = models.DateTimeField('Pendência resolvida em', null=True, blank=True)
    pendencia_resolvida_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name='Pendência resolvida por'
    )
    
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
    # Médico Atendente (Ambulatório)
    # Passa a referenciar médicos do ambulatório, vinculados por especialidade
    # O modelo MedicoAmbulatorio é declarado mais abaixo neste arquivo.
    medico_atendente = models.ForeignKey(
        'regulacao.MedicoAmbulatorio',
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
        ('pendente', 'Aguardando'),
        ('compareceu', 'Compareceu'),
        ('faltou', 'Faltou'),
    ]
    resultado_atendimento = models.CharField('Resultado do Atendimento', max_length=12, choices=RESULTADO_CHOICES, default='pendente', db_index=True)
    resultado_observacao = models.TextField('Observação do Resultado', blank=True)
    resultado_em = models.DateTimeField('Resultado registrado em', null=True, blank=True)
    resultado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name='Resultado registrado por')

    # Pendência (interação com UBS quando regulador necessita informação/ação)
    pendencia_motivo = models.TextField('Motivo da Pendência', blank=True,
                                        help_text='Descreva o que falta ou o que precisa ser corrigido pela UBS')
    pendencia_aberta_em = models.DateTimeField('Pendência aberta em', null=True, blank=True)
    pendencia_aberta_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name='Pendência aberta por'
    )
    pendencia_resposta = models.TextField('Resposta da UBS', blank=True)
    pendencia_respondida_em = models.DateTimeField('Pendência respondida em', null=True, blank=True)
    pendencia_respondida_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name='Resposta registrada por'
    )
    pendencia_resolvida_em = models.DateTimeField('Pendência resolvida em', null=True, blank=True)
    pendencia_resolvida_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name='Pendência resolvida por'
    )

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


class Notificacao(models.Model):
    """Notificações simples para avisar usuários sobre eventos relevantes.
    Ex.: respostas de pendências entre UBS e Regulação.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificacoes')
    texto = models.TextField()
    url = models.CharField(max_length=255, blank=True)
    lida = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['user', 'lida', 'criado_em']),
        ]

    def __str__(self):  # pragma: no cover
        return f"Notif para {self.user.username}: {self.texto[:40]}"


# ============ Histórico de Pendências (conversa) ============

class PendenciaMensagemExame(models.Model):
    """Mensagens trocadas na pendência de um exame (UBS ↔ Regulação)."""
    LADO_CHOICES = [
        ('ubs', 'UBS'),
        ('regulacao', 'Regulação'),
    ]
    TIPO_CHOICES = [
        ('mensagem', 'Mensagem'),
        ('abertura', 'Abertura da Pendência'),
    ]
    exame = models.ForeignKey('regulacao.RegulacaoExame', on_delete=models.CASCADE, related_name='pendencia_mensagens')
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    lado = models.CharField(max_length=20, choices=LADO_CHOICES)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='mensagem')
    texto = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['criado_em']
        indexes = [
            models.Index(fields=['exame', 'criado_em']),
        ]


class PendenciaMensagemConsulta(models.Model):
    """Mensagens trocadas na pendência de uma consulta (UBS ↔ Regulação)."""
    LADO_CHOICES = [
        ('ubs', 'UBS'),
        ('regulacao', 'Regulação'),
    ]
    TIPO_CHOICES = [
        ('mensagem', 'Mensagem'),
        ('abertura', 'Abertura da Pendência'),
    ]
    consulta = models.ForeignKey('regulacao.RegulacaoConsulta', on_delete=models.CASCADE, related_name='pendencia_mensagens')
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    lado = models.CharField(max_length=20, choices=LADO_CHOICES)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='mensagem')
    texto = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['criado_em']
        indexes = [
            models.Index(fields=['consulta', 'criado_em']),
        ]


# ============ Médicos do Ambulatório ============

class MedicoAmbulatorio(models.Model):
    """Médicos que atendem no ambulatório, vinculados a uma ou mais especialidades.
    Diferem dos Médicos Solicitantes (vinculados a UBS) e serão usados como "Médico Atendente" nas consultas.
    """
    nome = models.CharField('Nome do Médico', max_length=150)
    crm = models.CharField('CRM', max_length=20, unique=True)
    telefone = models.CharField('Telefone', max_length=30, blank=True)
    email = models.EmailField('E-mail', blank=True)
    ativo = models.BooleanField('Ativo', default=True)

    # Vínculo com Especialidades que este médico atende
    especialidades = models.ManyToManyField('regulacao.Especialidade', related_name='medicos_ambulatorio', blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Médico do Ambulatório'
        verbose_name_plural = 'Médicos do Ambulatório'
        ordering = ['nome']

    def __str__(self):
        return f"Dr(a). {self.nome} - CRM: {self.crm}"


# ============ Agenda Médica (semanal) ============

class AgendaMedica(models.Model):
    """Agenda semanal por Médico do Ambulatório e Especialidade.
    Define os dias da semana que atende e a capacidade (número de pacientes) por dia.
    """
    DIA_SEMANA_CHOICES = [
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    medico = models.ForeignKey('regulacao.MedicoAmbulatorio', on_delete=models.CASCADE, related_name='agendas')
    especialidade = models.ForeignKey('regulacao.Especialidade', on_delete=models.CASCADE, related_name='agendas_medicas')
    dia_semana = models.PositiveSmallIntegerField('Dia da Semana', choices=DIA_SEMANA_CHOICES)
    capacidade = models.PositiveIntegerField('Capacidade por dia', default=10, help_text='Número máximo de pacientes a atender nesse dia')
    ativo = models.BooleanField('Ativo', default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Agenda Médica'
        verbose_name_plural = 'Agendas Médicas'
        ordering = ['medico__nome', 'especialidade__nome', 'dia_semana']
        constraints = [
            models.UniqueConstraint(fields=['medico', 'especialidade', 'dia_semana'], name='uniq_agenda_medica_medico_especialidade_dia')
        ]
        indexes = [
            models.Index(fields=['medico', 'especialidade', 'dia_semana', 'ativo'])
        ]

    def __str__(self):  # pragma: no cover
        return f"{self.medico.nome} — {self.get_dia_semana_display()} ({self.especialidade.nome})"


# ============ Agenda Médica por Data (mensal) ============

class AgendaMedicaDia(models.Model):
    """Agenda por dia específico para Médico do Ambulatório e Especialidade.
    Permite definir a capacidade de atendimento em uma data concreta, predominando sobre a agenda semanal.
    """
    medico = models.ForeignKey('regulacao.MedicoAmbulatorio', on_delete=models.CASCADE, related_name='agendas_dia')
    especialidade = models.ForeignKey('regulacao.Especialidade', on_delete=models.CASCADE, related_name='agendas_medicas_dia')
    data = models.DateField('Data')
    capacidade = models.PositiveIntegerField('Capacidade do dia', default=10)
    ativo = models.BooleanField('Ativo', default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Agenda Médica (por dia)'
        verbose_name_plural = 'Agendas Médicas (por dia)'
        ordering = ['data', 'medico__nome']
        constraints = [
            models.UniqueConstraint(fields=['medico', 'especialidade', 'data'], name='uniq_agenda_medica_dia')
        ]
        indexes = [
            models.Index(fields=['medico', 'especialidade', 'data', 'ativo'])
        ]

    def __str__(self):  # pragma: no cover
        return f"{self.medico.nome} — {self.especialidade.nome} em {self.data:%d/%m/%Y}"


# ============ Registro de Ações dos Usuários ============

class AcaoUsuario(models.Model):
    """Registra todas as ações realizadas pelos usuários da regulação."""
    TIPO_ACAO_CHOICES = [
        ('autorizar_exame', 'Autorizar Exame'),
        ('negar_exame', 'Negar Exame'),
        ('pendenciar_exame', 'Pendenciar Exame'),
        ('autorizar_consulta', 'Autorizar Consulta'),
        ('negar_consulta', 'Negar Consulta'),
        ('pendenciar_consulta', 'Pendenciar Consulta'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='acoes_regulacao')
    tipo_acao = models.CharField('Tipo de Ação', max_length=30, choices=TIPO_ACAO_CHOICES)
    data_acao = models.DateTimeField('Data da Ação', auto_now_add=True)
    
    # Referências opcionais para exame ou consulta
    exame = models.ForeignKey('regulacao.RegulacaoExame', on_delete=models.CASCADE, null=True, blank=True)
    consulta = models.ForeignKey('regulacao.RegulacaoConsulta', on_delete=models.CASCADE, null=True, blank=True)
    
    # Informações adicionais
    paciente_nome = models.CharField('Nome do Paciente', max_length=200)
    motivo = models.TextField('Motivo/Observação', blank=True)
    
    class Meta:
        verbose_name = 'Ação do Usuário'
        verbose_name_plural = 'Ações dos Usuários'
        ordering = ['-data_acao']
        indexes = [
            models.Index(fields=['usuario', 'data_acao']),
            models.Index(fields=['tipo_acao', 'data_acao']),
        ]
    
    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_acao_display()} - {self.data_acao.strftime('%d/%m/%Y %H:%M')}"


