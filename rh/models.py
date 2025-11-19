from django.conf import settings
from django.db import models


class FuncionarioRH(models.Model):
    class Situacao(models.TextChoices):
        ATIVO = 'ativo', 'Ativo'
        INATIVO = 'inativo', 'Inativo'

    class Vinculo(models.TextChoices):
        CONCURSADO = 'concursado', 'Concursado'
        CELETISTA = 'celetista', 'Celetista'
        COMISSIONADO = 'comissionado', 'Comissionado'

    nome = models.CharField(max_length=150)
    cpf = models.CharField(max_length=11, unique=True)
    rg = models.CharField(max_length=20, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField()

    cargo = models.CharField(max_length=100)
    situacao = models.CharField(max_length=10, choices=Situacao.choices, default=Situacao.ATIVO)
    vinculo = models.CharField(max_length=15, choices=Vinculo.choices, default=Vinculo.CONCURSADO)

    data_admissao = models.DateField(null=True, blank=True)
    data_desligamento = models.DateField(null=True, blank=True)

    # Endereço
    cep = models.CharField(max_length=8, blank=True)
    endereco = models.CharField(max_length=200, blank=True)
    numero = models.CharField(max_length=20, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    uf = models.CharField(max_length=2, blank=True)

    setor_lotacao = models.CharField(max_length=120, blank=True)

    observacoes = models.TextField(blank=True)

    # Documentos
    doc_rg = models.FileField(upload_to='rh/docs/rg/', blank=True, null=True)
    doc_ctps = models.FileField(upload_to='rh/docs/ctps/', blank=True, null=True)
    doc_comprovante_endereco = models.FileField(upload_to='rh/docs/comprovantes/', blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Funcionário (RH)'
        verbose_name_plural = 'Funcionários (RH)'

    def __str__(self) -> str:
        return f"{self.nome} ({self.cargo})"


class AtestadoMedico(models.Model):
    """Registro de atestados médicos vinculados ao funcionário do RH.
    Permite múltiplos atestados por funcionário, com período, CID e arquivo.
    """
    funcionario = models.ForeignKey(
        FuncionarioRH,
        on_delete=models.CASCADE,
        related_name='atestados'
    )
    data_inicio = models.DateField('Data inicial')
    data_fim = models.DateField('Data final')
    dias = models.PositiveIntegerField('Dias de afastamento', default=1)
    cid = models.CharField('CID (opcional)', max_length=15, blank=True)
    medico = models.CharField('Médico (opcional)', max_length=150, blank=True)
    crm = models.CharField('CRM (opcional)', max_length=30, blank=True)
    motivo = models.TextField('Motivo/Observações', blank=True)
    arquivo = models.FileField('Arquivo do Atestado', upload_to='rh/atestados/', null=True, blank=True)
    ativo = models.BooleanField('Ativo', default=True)
    removido_em = models.DateTimeField('Removido em', null=True, blank=True)
    removido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='atestados_removidos',
        verbose_name='Removido por',
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_inicio', '-criado_em']
        verbose_name = 'Atestado Médico'
        verbose_name_plural = 'Atestados Médicos'
        indexes = [
            models.Index(fields=['funcionario', 'data_inicio']),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"Atestado de {self.funcionario.nome} ({self.data_inicio:%d/%m/%Y} - {self.data_fim:%d/%m/%Y})"
