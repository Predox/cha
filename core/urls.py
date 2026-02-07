from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),

    # Setup inicial
    path("setup/<str:token>/", views.setup, name="setup"),

    # Auth
    path("login/", views.login_codigo, name="login_codigo"),
    path("login/verificar/", views.verificar_codigo, name="verificar_codigo"),
    path("login/senha/", views.login_senha, name="login_senha"),
    path("sair/", views.sair, name="sair"),
    path("esqueci-senha/", views.esqueci_senha, name="esqueci_senha"),
    path("redefinir-senha/", views.redefinir_senha, name="redefinir_senha"),
    path("definir-senha/", views.definir_senha, name="definir_senha"),

    # Catálogo
    path("catalogo/", views.catalogo, name="catalogo"),
    path("meus-presentes/", views.meus_presentes, name="meus_presentes"),
    path("presentes/<int:gift_id>/reservar/", views.reservar_presente, name="reservar_presente"),
    path("presentes/<int:gift_id>/cancelar/", views.cancelar_reserva, name="cancelar_reserva"),

    # Painel do casal
    path("painel/", views.painel_dashboard, name="painel_dashboard"),
    path("painel/presentes/", views.painel_presentes, name="painel_presentes"),
    path("painel/presentes/novo/", views.painel_presente_novo, name="painel_presente_novo"),
    path("painel/presentes/<int:gift_id>/editar/", views.painel_presente_editar, name="painel_presente_editar"),
    path("painel/presentes/<int:gift_id>/excluir/", views.painel_presente_excluir, name="painel_presente_excluir"),
    path("painel/personalizacao/", views.painel_personalizacao, name="painel_personalizacao"),
    path("painel/mensagens/", views.painel_mensagens, name="painel_mensagens"),
]
