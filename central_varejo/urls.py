from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views
from produtos import views as produtos_views
from estoque import views as estoque_views
from vendas import views as vendas_views

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    # Autenticação
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    # Página inicial protegida
    path("", views.inicio, name="inicio"),
    path("produtos/", produtos_views.listar_produtos, name="listar_produtos"),
    path(
        "produtos/cadastrar/",
        produtos_views.cadastrar_produto,
        name="cadastrar_produto",
    ),
    path(
        "produtos/editar/<int:produto_id>/",
        produtos_views.editar_produto,
        name="editar_produto",
    ),
    path(
        "produtos/desativar/<int:produto_id>/",
        produtos_views.desativar_produto,
        name="desativar_produto",
    ),
    path(
        "estoque/entrada/",
        estoque_views.registrar_entrada,
        name="registrar_entrada",
    ),
    path(
        "estoque/ajuste/",
        estoque_views.registrar_ajuste,
        name="registrar_ajuste",
    ),
    path(
        "estoque/historico/",
        estoque_views.historico_movimentacoes,
        name="historico_movimentacoes",
    ),
    path(
        "estoque/",
        estoque_views.consultar_estoque,
        name="consultar_estoque",
    ),
    # Vendas
    path(
        "vendas/nova/",
        vendas_views.iniciar_venda,
        name="iniciar_venda",
    ),
    path(
        "vendas/carrinho/atualizar/<int:produto_id>/",
        vendas_views.atualizar_quantidade,
        name="atualizar_quantidade_venda",
    ),
    path(
        "vendas/carrinho/remover/<int:produto_id>/",
        vendas_views.remover_produto,
        name="remover_produto_venda",
    ),
    path(
        "vendas/finalizar/",
        vendas_views.finalizar_venda,
        name="finalizar_venda",
    ),
    path(
        "vendas/historico/",
        vendas_views.historico_vendas,
        name="historico_vendas",
    ),
    path(
        "vendas/historico/<int:venda_id>/",
        vendas_views.detalhes_venda,
        name="detalhes_venda",
    ),
    path("relatorios/", include("relatorios.urls")),
]
