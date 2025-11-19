from django.urls import path
from . import views
from .views import minhas_notificacoes, notificacao_marcar_lida

urlpatterns = [
    # Dashboard
    path('', views.dashboard_regulacao, name='regulacao-dashboard'),
    path('o-que-fiz-hoje/', views.o_que_fiz_hoje, name='o-que-fiz-hoje'),
    path('malote/', views.selecionar_malote, name='regulacao-selecionar-malote'),
    path('fila/', views.fila_espera, name='regulacao-fila'),
    path('agenda/', views.agenda_regulacao, name='regulacao-agenda'),
    path('ubs/<int:ubs_id>/status/', views.status_ubs, name='regulacao-status-ubs'),
    
    # UBS
    path('ubs/', views.UBSListView.as_view(), name='ubs-list'),
    path('ubs/nova/', views.UBSCreateView.as_view(), name='ubs-create'),
    path('ubs/editar/<int:pk>/', views.UBSUpdateView.as_view(), name='ubs-update'),
    path('ubs/excluir/<int:pk>/', views.UBSDeleteView.as_view(), name='ubs-delete'),

    # Locais de Atendimento
    path('locais/', views.LocalAtendimentoListView.as_view(), name='localatendimento-list'),
    path('locais/novo/', views.LocalAtendimentoCreateView.as_view(), name='localatendimento-create'),
    path('locais/editar/<int:pk>/', views.LocalAtendimentoUpdateView.as_view(), name='localatendimento-update'),
    path('locais/excluir/<int:pk>/', views.LocalAtendimentoDeleteView.as_view(), name='localatendimento-delete'),
    
    # Médicos
    path('medicos/', views.MedicoListView.as_view(), name='medico-list'),
    path('medicos/novo/', views.MedicoCreateView.as_view(), name='medico-create'),
    path('medicos/editar/<int:pk>/', views.MedicoUpdateView.as_view(), name='medico-update'),
    path('medicos/excluir/<int:pk>/', views.MedicoDeleteView.as_view(), name='medico-delete'),
    # Médicos do Ambulatório
    path('ambulatorio/medicos/', views.MedicoAmbulatorioListView.as_view(), name='ambulatorio-medico-list'),
    path('ambulatorio/medicos/novo/', views.MedicoAmbulatorioCreateView.as_view(), name='ambulatorio-medico-create'),
    path('ambulatorio/medicos/editar/<int:pk>/', views.MedicoAmbulatorioUpdateView.as_view(), name='ambulatorio-medico-update'),
    path('ambulatorio/medicos/excluir/<int:pk>/', views.MedicoAmbulatorioDeleteView.as_view(), name='ambulatorio-medico-delete'),
    # Agenda Médica (mensal - por dia) COMO PÁGINA PRINCIPAL
    path('ambulatorio/agenda/', views.AgendaMedicaDiaListView.as_view(), name='agendamedica-list'),
    path('ambulatorio/agenda/nova/', views.agenda_mensal_gerar, name='agendamedica-create'),
    path('ambulatorio/agenda/editar/<int:pk>/', views.AgendaMedicaDiaUpdateView.as_view(), name='agendamedica-update'),
    path('ambulatorio/agenda/excluir/<int:pk>/', views.AgendaMedicaDiaDeleteView.as_view(), name='agendamedica-delete'),
    # Ajax info
    path('ambulatorio/agenda/info/', views.agenda_info, name='agendamedica-info'),

    # Agenda Médica por Dia (CRUD + Gerador)
    path('ambulatorio/agenda-dia/', views.AgendaMedicaDiaListView.as_view(), name='agendadia-list'),
    path('ambulatorio/agenda-dia/nova/', views.AgendaMedicaDiaCreateView.as_view(), name='agendadia-create'),
    path('ambulatorio/agenda-dia/editar/<int:pk>/', views.AgendaMedicaDiaUpdateView.as_view(), name='agendadia-update'),
    path('ambulatorio/agenda-dia/excluir/<int:pk>/', views.AgendaMedicaDiaDeleteView.as_view(), name='agendadia-delete'),
    path('ambulatorio/agenda-dia/gerar/', views.agenda_mensal_gerar, name='agendadia-gerar'),
    
    # Tipos de Exames
    path('tipos-exame/', views.TipoExameListView.as_view(), name='tipo-exame-list'),
    path('tipos-exame/importar/', views.importar_sigtap, name='importar-sigtap'),
    path('tipos-exame/novo/', views.TipoExameCreateView.as_view(), name='tipo-exame-create'),
    path('tipos-exame/editar/<int:pk>/', views.TipoExameUpdateView.as_view(), name='tipo-exame-update'),
    path('tipos-exame/excluir/<int:pk>/', views.TipoExameDeleteView.as_view(), name='tipo-exame-delete'),
    path('tipos-exame/<int:pk>/toggle-ativo/', views.tipo_exame_toggle_ativo, name='tipo-exame-toggle-ativo'),
    
    # Especialidades (Consultas)
    path('especialidades/', views.EspecialidadeListView.as_view(), name='especialidade-list'),
    path('especialidades/nova/', views.EspecialidadeCreateView.as_view(), name='especialidade-create'),
    path('especialidades/editar/<int:pk>/', views.EspecialidadeUpdateView.as_view(), name='especialidade-update'),
    path('especialidades/excluir/<int:pk>/', views.EspecialidadeDeleteView.as_view(), name='especialidade-delete'),

    # Regulação de Consultas
    path('consultas/', views.RegulacaoConsultaListView.as_view(), name='consulta-list'),
    path('consultas/nova/', views.RegulacaoConsultaCreateView.as_view(), name='consulta-create'),
    path('consultas/<int:pk>/', views.RegulacaoConsultaDetailView.as_view(), name='consulta-detail'),
    path('consultas/<int:pk>/editar/', views.RegulacaoConsultaUpdateView.as_view(), name='consulta-update'),
    path('consultas/<int:pk>/excluir/', views.RegulacaoConsultaDeleteView.as_view(), name='consulta-delete'),
    path('consultas/<int:pk>/regular/', views.regular_consulta, name='regular-consulta'),
    # Comprovantes removidos (consultas)
    # Auxiliar (AJAX) - alertas de consultas por paciente
    path('consultas/alertas/', views.consulta_paciente_alertas, name='consulta-alertas'),

    # Regulação de Exames
    path('regulacao/', views.RegulacaoListView.as_view(), name='regulacao-list'),
    path('regulacao/nova/', views.RegulacaoCreateView.as_view(), name='regulacao-create'),
    path('regulacao/<int:pk>/', views.RegulacaoDetailView.as_view(), name='regulacao-detail'),
    path('regulacao/<int:pk>/editar/', views.RegulacaoUpdateView.as_view(), name='regulacao-update'),
    path('regulacao/<int:pk>/excluir/', views.RegulacaoDeleteView.as_view(), name='regulacao-delete'),
    # Rota antiga de regularização por item removida em favor do fluxo por paciente
    # Página por paciente
    path('paciente/<int:paciente_id>/pedido/', views.paciente_pedido, name='paciente-pedido'),
    # Comprovantes removidos (exames)
    # Resultado de atendimento (Compareceu/Faltou)
    path('regulacao/<int:pk>/resultado/', views.registrar_resultado_exame, name='resultado-exame'),
    path('consultas/<int:pk>/resultado/', views.registrar_resultado_consulta, name='resultado-consulta'),
    path('agenda/resultado/batch/', views.registrar_resultados_agenda, name='agenda-resultado-batch'),
    # Impressão (novo fluxo)
    # path('consultas/<int:pk>/impressao/', views.impressao_consulta, name='impressao-consulta'),
    path('consultas/paciente/<int:paciente_id>/dia/<slug:dia>/impressao/', views.impressao_consultas_dia, name='impressao-consultas-dia'),
    path('exames/paciente/<int:paciente_id>/dia/<slug:dia>/impressao/', views.impressao_exames_dia, name='impressao-exames-dia'),
    # Pendências (resposta UBS)
    path('pendencia/exame/<int:pk>/responder/', views.responder_pendencia_exame, name='pendencia-exame-responder'),
    path('pendencia/consulta/<int:pk>/responder/', views.responder_pendencia_consulta, name='pendencia-consulta-responder'),
    # Edição de textos (Obs/Motivo/Pendência)
    path('texto/exame/<int:pk>/editar/', views.editar_textos_exame, name='texto-exame-editar'),
    path('texto/consulta/<int:pk>/editar/', views.editar_textos_consulta, name='texto-consulta-editar'),
    # Auxiliar (AJAX) - alertas de exames por paciente
    path('regulacao/alertas/', views.exame_paciente_alertas, name='exame-alertas'),
    # Notificações
    path('notificacoes/', minhas_notificacoes, name='notificacoes-list'),
    path('notificacoes/<int:pk>/lida/', notificacao_marcar_lida, name='notificacao-lida'),
    path('salvar-acao-ajax/', views.salvar_acao_ajax, name='salvar-acao-ajax'),
]