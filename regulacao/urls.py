from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard_regulacao, name='regulacao-dashboard'),
    path('fila/', views.fila_espera, name='regulacao-fila'),
    path('agenda/', views.agenda_regulacao, name='regulacao-agenda'),
    path('ubs/<int:ubs_id>/status/', views.status_ubs, name='regulacao-status-ubs'),
    
    # UBS
    path('ubs/', views.UBSListView.as_view(), name='ubs-list'),
    path('ubs/nova/', views.UBSCreateView.as_view(), name='ubs-create'),
    path('ubs/editar/<int:pk>/', views.UBSUpdateView.as_view(), name='ubs-update'),
    path('ubs/excluir/<int:pk>/', views.UBSDeleteView.as_view(), name='ubs-delete'),
    
    # Médicos
    path('medicos/', views.MedicoListView.as_view(), name='medico-list'),
    path('medicos/novo/', views.MedicoCreateView.as_view(), name='medico-create'),
    path('medicos/editar/<int:pk>/', views.MedicoUpdateView.as_view(), name='medico-update'),
    path('medicos/excluir/<int:pk>/', views.MedicoDeleteView.as_view(), name='medico-delete'),
    
    # Tipos de Exames
    path('tipos-exame/', views.TipoExameListView.as_view(), name='tipo-exame-list'),
    path('tipos-exame/importar/', views.importar_sigtap, name='importar-sigtap'),
    path('tipos-exame/novo/', views.TipoExameCreateView.as_view(), name='tipo-exame-create'),
    path('tipos-exame/editar/<int:pk>/', views.TipoExameUpdateView.as_view(), name='tipo-exame-update'),
    path('tipos-exame/excluir/<int:pk>/', views.TipoExameDeleteView.as_view(), name='tipo-exame-delete'),
    
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
    # Comprovantes (Consultas)
    path('consultas/<int:pk>/comprovante/', views.comprovante_consulta, name='comprovante-consulta'),
    path('consultas/comprovantes/', views.comprovantes_consultas, name='comprovantes-consultas'),
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
    # Comprovantes (Exames)
    path('regulacao/<int:pk>/comprovante/', views.comprovante_exame, name='comprovante-exame'),
    path('regulacao/comprovantes/', views.comprovantes_exames, name='comprovantes-exames'),
    # Resultado de atendimento (Compareceu/Faltou)
    path('regulacao/<int:pk>/resultado/', views.registrar_resultado_exame, name='resultado-exame'),
    path('consultas/<int:pk>/resultado/', views.registrar_resultado_consulta, name='resultado-consulta'),
    # Auxiliar (AJAX) - alertas de exames por paciente
    path('regulacao/alertas/', views.exame_paciente_alertas, name='exame-alertas'),
]