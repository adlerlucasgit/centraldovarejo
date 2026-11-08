from django.urls import path

from . import views

urlpatterns = [
    path("", views.listar_usuarios, name="listar_usuarios"),
    path("cadastrar/", views.cadastrar_usuario, name="cadastrar_usuario"),
    path(
        "<int:usuario_id>/editar/",
        views.editar_usuario,
        name="editar_usuario",
    ),
    path(
        "<int:usuario_id>/suspender/",
        views.suspender_usuario,
        name="suspender_usuario",
    ),
    path(
        "<int:usuario_id>/reativar/",
        views.reativar_usuario,
        name="reativar_usuario",
    ),
    path(
        "<int:usuario_id>/excluir/",
        views.excluir_usuario,
        name="excluir_usuario",
    ),
]
