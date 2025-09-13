from django.db import models
from decimal import Decimal


class TFD(models.Model):
	"""Tratamento Fora do Domicílio (registro da viagem/benefício).

	Permite vincular a um `pacientes.Paciente` existente, mas também
	armazena uma cópia dos dados principais do paciente (nome, CPF, CNS,
	endereço, telefone) para histórico/portabilidade.
	"""
	paciente = models.ForeignKey(
		'pacientes.Paciente', on_delete=models.SET_NULL, null=True, blank=True,
		help_text='Opcional: vincular a um paciente já cadastrado')

	# snapshot dos dados pessoais (preenchidos automaticamente se paciente informado)
	paciente_nome = models.CharField('Nome do paciente', max_length=150)
	paciente_cpf = models.CharField('CPF', max_length=14, blank=True, null=True)
	paciente_cns = models.CharField('CNS', max_length=20, blank=True, null=True)
	paciente_endereco = models.TextField('Endereço', max_length=300, blank=True)
	paciente_telefone = models.CharField('Telefone', max_length=30, blank=True)

	# cidades
	cidade_origem = models.CharField('Cidade de origem', max_length=100, default='Iturama', editable=False)
	cidade_destino = models.CharField('Cidade de destino', max_length=150, blank=True)

	# período da viagem/benefício
	data_inicio = models.DateField('Data início', null=True, blank=True)
	data_fim = models.DateField('Data fim', null=True, blank=True)
	numero_diarias = models.PositiveIntegerField('Número de diárias', default=1)
	valor_diaria = models.DecimalField('Valor da diária', max_digits=10, decimal_places=2)
	# novo campo: valor do benefício
	valor_beneficio = models.DecimalField('Valor do benefício', max_digits=12, decimal_places=2, default=0)
	valor_total = models.DecimalField('Valor total', max_digits=12, decimal_places=2)

	observacoes = models.TextField('Observações', blank=True)

	# NOTE: assinatura/autoriza fields removed (stored signatures/authorization no longer kept)

	criado_em = models.DateTimeField(auto_now_add=True)
	atualizado_em = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = 'TFD'
		verbose_name_plural = 'TFD'
		ordering = ['-data_inicio', '-criado_em']

	def __str__(self):
		di = self.data_inicio.isoformat() if self.data_inicio else '—'
		df = self.data_fim.isoformat() if self.data_fim else '—'
		return f"TFD: {self.paciente_nome} — {self.cidade_destino or '—'} — {di} to {df}"

	def save(self, *args, **kwargs):
		"""Se houver paciente vinculado e campos snapshot vazios, preenche-os.

		Também calcula `valor_total` como `valor_diaria * numero_diarias` se
		o usuário não forneceu explicitamente outro valor.
		"""
		# preencher snapshot se possível
		if self.paciente:
			try:
				p = self.paciente
				# só preenche quando os campos estiverem vazios
				if not self.paciente_nome:
					self.paciente_nome = p.nome
				if not self.paciente_cpf and getattr(p, 'cpf', None):
					self.paciente_cpf = p.cpf
				if not self.paciente_cns and getattr(p, 'cns', None):
					self.paciente_cns = p.cns
				if (not self.paciente_endereco) and getattr(p, 'endereco', None):
					self.paciente_endereco = p.endereco
				if (not self.paciente_telefone) and getattr(p, 'telefone', None):
					self.paciente_telefone = p.telefone
			except Exception:
				pass

		# calcular número de diárias a partir das datas quando não informado
		try:
			if (not self.numero_diarias or self.numero_diarias == 0) and self.data_inicio and self.data_fim:
				delta = (self.data_fim - self.data_inicio).days + 1
				self.numero_diarias = max(1, delta)
		except Exception:
			pass

		# recalcular sempre o valor_total como valor_beneficio + (valor_diaria * numero_diarias)
		try:
			if self.valor_diaria is not None:
				beneficio = self.valor_beneficio or Decimal('0')
				# garantir que numero_diarias seja Decimal para multiplicação correta
				num = Decimal(self.numero_diarias)
				self.valor_total = (self.valor_diaria * num) + beneficio
		except Exception:
			# em caso de erro de multiplicação (tipo), deixar como está e deixar o DB reportar
			pass

		# authorization/signature fields removed; no-op

		super().save(*args, **kwargs)
