from django.db import models
from veiculos.models import Veiculo


class Motorista(models.Model):
    ATIVO_INATIVO = (
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo'),
    )
    # Dados pessoais
    nome_completo = models.CharField(max_length=150)
    # Permite CPF com máscara (XXX.XXX.XXX-XX) ou apenas dígitos; validação e limpeza ficam no formulário
    cpf = models.CharField(max_length=14, unique=True, blank=True, null=True)
    rg = models.CharField(max_length=20, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)

    # CNH
    cnh_numero = models.CharField(max_length=20, blank=True)
    cnh_categoria = models.CharField(max_length=5, blank=True)
    cnh_validade = models.DateField(null=True, blank=True)

    # Contato e Endereço
    endereco = models.CharField(max_length=255, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    # Dados funcionais
    matricula = models.CharField(max_length=50, blank=True)
    data_admissao = models.DateField(null=True, blank=True)
    situacao = models.CharField(max_length=10, choices=ATIVO_INATIVO, default='ativo')
    escala_trabalho = models.CharField(max_length=100, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome_completo']

    def __str__(self):
        return self.nome_completo

    def save(self, *args, **kwargs):
        # Garantir nome em MAIÚSCULAS no banco
        if self.nome_completo:
            self.nome_completo = (self.nome_completo or '').strip().upper()
        super().save(*args, **kwargs)


class ViagemMotorista(models.Model):
    motorista = models.ForeignKey(Motorista, on_delete=models.CASCADE, related_name='viagens')

    # Identificação da viagem
    codigo = models.CharField('Código/ID da viagem', max_length=50)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    origem = models.CharField('Local de origem', max_length=150)
    destino = models.CharField('Local de destino', max_length=150)
    veiculo = models.ForeignKey(Veiculo, on_delete=models.SET_NULL, null=True, blank=True)

    # Controle financeiro e operacional
    dias_viagem = models.PositiveIntegerField(default=0)
    quantidade_diarias = models.PositiveIntegerField(default=0)
    valor_unitario_diaria = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_total_diarias = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    quantidade_horas_extras = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    valor_hora_extra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_total_horas_extras = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    justificativa_horas_extras = models.TextField(blank=True)

    # Observações adicionais
    motivo_viagem = models.CharField(max_length=255, blank=True)
    observacoes = models.TextField(blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_inicio', '-id']

    def __str__(self):
        return f"{self.codigo} - {self.motorista.nome_completo}"

    def save(self, *args, **kwargs):
        # Forçar origem padrão
        self.origem = 'Iturama'
        # Calcular dias de viagem sempre com inclusão (mesmo dia = 1)
        if self.data_inicio and self.data_fim:
            delta = (self.data_fim - self.data_inicio).days + 1
            self.dias_viagem = max(delta, 0)
            # Quantidade de diárias acompanha dias de viagem
            self.quantidade_diarias = self.dias_viagem
        # Recalcular totais
        self.valor_total_diarias = (self.quantidade_diarias or 0) * (self.valor_unitario_diaria or 0)
        self.valor_total_horas_extras = (self.quantidade_horas_extras or 0) * (self.valor_hora_extra or 0)
        # Gerar código/ID automaticamente se não informado
        if not (self.codigo or '').strip():
            from django.utils import timezone
            base = f"VG{timezone.localdate().strftime('%Y%m%d')}"
            seq = 1
            codigo = f"{base}-{seq:03d}"
            while type(self).objects.filter(codigo=codigo).exists():
                seq += 1
                codigo = f"{base}-{seq:03d}"
            self.codigo = codigo
        super().save(*args, **kwargs)
