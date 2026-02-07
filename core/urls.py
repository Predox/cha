from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),

    # Setup inicial
    path("setup/<str:token>/", views.setup, name="setup"),

    # Auth
    path("login/", views.login_view, name="login"),
    path("cadastro/", views.cadastro, name="cadastro"),
    path("sair/", views.sair, name="sair"),
    path("definir-senha/", views.definir_senha, name="definir_senha"),

    # Catalogo
    path("catalogo/", views.catalogo, name="catalogo"),
    path("meus-presentes/", views.meus_presentes, name="meus_presentes"),
    path("presentes/<int:gift_id>/reservar/", views.reservar_presente, name="reservar_presente"),
    path("presentes/<int:gift_id>/cancelar/", views.cancelar_reserva, name="cancelar_reserva"),

    # Painel admin
    path("painel/", views.painel_dashboard, name="painel_dashboard"),
    path("painel/presentes/", views.painel_presentes, name="painel_presentes"),
    path("painel/presentes/novo/", views.painel_presente_novo, name="painel_presente_novo"),
    path("painel/presentes/<int:gift_id>/editar/", views.painel_presente_editar, name="painel_presente_editar"),
    path("painel/presentes/<int:gift_id>/excluir/", views.painel_presente_excluir, name="painel_presente_excluir"),
    path("painel/personalizacao/", views.painel_personalizacao, name="painel_personalizacao"),
    path("painel/mensagens/", views.painel_mensagens, name="painel_mensagens"),
    path("painel/mensagens/<int:reservation_id>/visto/", views.marcar_mensagem_vista, name="marcar_mensagem_vista"),
    path("painel/mensagens/vistas/", views.marcar_todas_mensagens_vistas, name="marcar_todas_mensagens_vistas"),

    # Observador
    path("observador/mensagens/", views.observador_mensagens, name="observador_mensagens"),
    path(
        "observador/mensagens/<int:reservation_id>/ocultar/",
        views.observador_ocultar_mensagem,
        name="observador_ocultar_mensagem",
    ),
    path(
        "observador/mensagens/<int:reservation_id>/mostrar/",
        views.observador_mostrar_mensagem,
        name="observador_mostrar_mensagem",
    ),
    path(
        "observador/mensagens/<int:reservation_id>/excluir/",
        views.observador_excluir_mensagem,
        name="observador_excluir_mensagem",
    ),
    path(
        "observador/usuarios/<int:user_id>/senha/",
        views.observador_alterar_senha,
        name="observador_alterar_senha",
    ),
    path(
        "observador/usuarios/<int:user_id>/reservas/remover/",
        views.observador_remover_reservas,
        name="observador_remover_reservas",
    ),
]
