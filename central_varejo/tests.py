from datetime import timedelta
from central_varejo.context_processors import perfil_usuario
from types import SimpleNamespace
from django.contrib.auth.models import AnonymousUser
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from produtos.models import Produto
from estoque.models import Estoque
from vendas.models import Venda

User = get_user_model()


class DashboardTests(TestCase):

    def setUp(self):
        grupo_admin, _ = Group.objects.get_or_create(name="Administrador")
        grupo_caixa, _ = Group.objects.get_or_create(name="Caixa")

        self.admin = User.objects.create_user(
            username="admin_dashboard",
            password="senha_teste_123",
        )
        self.admin.groups.add(grupo_admin)

        self.caixa = User.objects.create_user(
            username="caixa_dashboard",
            password="senha_teste_123",
        )
        self.caixa.groups.add(grupo_caixa)

        self.outro_caixa = User.objects.create_user(
            username="outro_dashboard",
            password="senha_teste_123",
        )
        self.outro_caixa.groups.add(grupo_caixa)

        self.produto1 = Produto.objects.create(
            codigo="DASH001",
            nome="Produto Dashboard A",
            preco=Decimal("20.00"),
        )

        self.produto2 = Produto.objects.create(
            codigo="DASH002",
            nome="Produto Dashboard B",
            preco=Decimal("30.00"),
        )

        Estoque.objects.filter(produto=self.produto1).update(current_stock=10)
        Estoque.objects.filter(produto=self.produto2).update(current_stock=5)

        hoje = timezone.localdate()

        self.venda1 = Venda.objects.create(
            number="DASH-VENDA-001",
            user=self.caixa,
            total=Decimal("100.00"),
            payment_method=Venda.FormaPagamento.PIX,
        )

        self.venda2 = Venda.objects.create(
            number="DASH-VENDA-002",
            user=self.outro_caixa,
            total=Decimal("50.00"),
            payment_method=Venda.FormaPagamento.DINHEIRO,
        )

        Venda.objects.filter(pk=self.venda1.pk).update(
            date_time=timezone.make_aware(
                timezone.datetime(hoje.year, hoje.month, hoje.day, 10, 0)
            )
        )

        Venda.objects.filter(pk=self.venda2.pk).update(
            date_time=timezone.make_aware(
                timezone.datetime(hoje.year, hoje.month, hoje.day, 11, 0)
            )
        )

    def test_administrador_acessa_dashboard(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("inicio"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inicio.html")

    def test_caixa_acessa_dashboard(self):
        self.client.force_login(self.caixa)
        response = self.client.get(reverse("inicio"))

        self.assertEqual(response.status_code, 200)

    def test_usuario_sem_grupo_nao_acessa_dashboard(self):
        usuario = User.objects.create_user(
            username="usuario_dashboard",
            password="senha_teste_123",
        )

        self.client.force_login(usuario)
        response = self.client.get(reverse("inicio"))

        self.assertEqual(response.status_code, 403)

    def test_usuario_nao_autenticado_e_redirecionado(self):
        response = self.client.get(reverse("inicio"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_administrador_visualiza_vendas_de_todos_os_caixas(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("inicio"))

        vendas = list(response.context["vendas_recentes"])

        self.assertEqual(len(vendas), 2)
        self.assertIn(self.venda1, vendas)
        self.assertIn(self.venda2, vendas)

    def test_caixa_visualiza_somente_suas_vendas(self):
        self.client.force_login(self.caixa)
        response = self.client.get(reverse("inicio"))

        vendas = list(response.context["vendas_recentes"])

        self.assertEqual(len(vendas), 1)
        self.assertEqual(vendas[0], self.venda1)

    def test_calcular_indicadores_do_dashboard(self):
        Estoque.objects.filter(produto=self.produto2).update(
            current_stock=0
        )

        self.client.force_login(self.admin)
        response = self.client.get(reverse("inicio"))

        self.assertEqual(response.context["total_produtos"], 2)
        self.assertEqual(response.context["itens_em_estoque"], 10)
        self.assertEqual(response.context["alertas_estoque_baixo"], 1)
        self.assertEqual(
            response.context["total_vendas_dia"],
            Decimal("150.00"),
    )

    def test_filtrar_dashboard_por_data(self):
        self.client.force_login(self.admin)
        ontem = timezone.localdate() - timedelta(days=1)

        response = self.client.get(
            reverse("inicio"),
            {"data": ontem.isoformat()},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["data_selecionada"], ontem)
        self.assertEqual(
            response.context["total_vendas_dia"],
            Decimal("0"),
        )

    def test_data_invalida_utiliza_data_atual(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("inicio"),
            {"data": "data-invalida"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["data_selecionada"],
            timezone.localdate(),
        )


class LoginTests(TestCase):

    def test_acessar_pagina_de_login(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "registration/login.html",
        )

    def test_login_com_credenciais_validas(self):
        grupo_caixa, _ = Group.objects.get_or_create(name="Caixa")

        usuario = User.objects.create_user(
            username="login_teste",
            password="senha_teste_123",
        )
        usuario.groups.add(grupo_caixa)

        response = self.client.post(
            reverse("login"),
            {
                "username": "login_teste",
                "password": "senha_teste_123",
            },
        )

        self.assertRedirects(response, reverse("inicio"))
        self.assertTrue(self.client.session.get("_auth_user_id"))

    def test_login_com_senha_incorreta(self):
        User.objects.create_user(
            username="login_invalido",
            password="senha_teste_123",
        )

        response = self.client.post(
            reverse("login"),
            {
                "username": "login_invalido",
                "password": "senha_errada",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())

    def test_logout(self):
        usuario = User.objects.create_user(
            username="logout_teste",
            password="senha_teste_123",
        )

        self.client.force_login(usuario)
        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)


from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser


class PerfilUsuarioTests(TestCase):

    def setUp(self):
        self.grupo_admin, _ = Group.objects.get_or_create(name="Administrador")
        self.grupo_caixa, _ = Group.objects.get_or_create(name="Caixa")

    def test_usuario_nao_autenticado_nao_recebe_permissoes(self):
        request = SimpleNamespace(user=AnonymousUser())

        contexto = perfil_usuario(request)

        self.assertFalse(contexto["eh_administrador"])
        self.assertFalse(contexto["eh_caixa"])
        self.assertFalse(contexto["pode_operar_vendas"])
        self.assertFalse(contexto["pode_consultar_estoque"])
        self.assertFalse(contexto["pode_gerenciar_estoque"])
        self.assertFalse(contexto["pode_ver_relatorios"])

    def test_superusuario_recebe_permissoes_administrativas(self):
        usuario = User.objects.create_superuser(
            username="super_contexto",
            email="super@teste.com",
            password="SenhaForte@2026",
        )

        request = SimpleNamespace(user=usuario)

        contexto = perfil_usuario(request)

        self.assertTrue(contexto["eh_administrador"])
        self.assertFalse(contexto["eh_caixa"])
        self.assertTrue(contexto["pode_operar_vendas"])
        self.assertTrue(contexto["pode_consultar_estoque"])
        self.assertTrue(contexto["pode_gerenciar_estoque"])
        self.assertTrue(contexto["pode_ver_relatorios"])

    def test_usuario_administrador_recebe_permissoes_corretas(self):
        usuario = User.objects.create_user(
            username="admin_contexto",
            password="senha_teste_123",
        )
        usuario.groups.add(self.grupo_admin)

        request = SimpleNamespace(user=usuario)

        contexto = perfil_usuario(request)

        self.assertTrue(contexto["eh_administrador"])
        self.assertFalse(contexto["eh_caixa"])
        self.assertTrue(contexto["pode_gerenciar_estoque"])
        self.assertTrue(contexto["pode_ver_relatorios"])

    def test_usuario_caixa_recebe_permissoes_restritas(self):
        usuario = User.objects.create_user(
            username="caixa_contexto",
            password="senha_teste_123",
        )
        usuario.groups.add(self.grupo_caixa)

        request = SimpleNamespace(user=usuario)

        contexto = perfil_usuario(request)

        self.assertFalse(contexto["eh_administrador"])
        self.assertTrue(contexto["eh_caixa"])
        self.assertTrue(contexto["pode_operar_vendas"])
        self.assertTrue(contexto["pode_consultar_estoque"])
        self.assertFalse(contexto["pode_gerenciar_estoque"])
        self.assertFalse(contexto["pode_ver_relatorios"])

    def test_administrador_tem_prioridade_sobre_caixa(self):
        usuario = User.objects.create_user(
            username="admin_caixa_contexto",
            password="senha_teste_123",
        )
        usuario.groups.add(self.grupo_admin, self.grupo_caixa)

        request = SimpleNamespace(user=usuario)

        contexto = perfil_usuario(request)

        self.assertTrue(contexto["eh_administrador"])
        self.assertFalse(contexto["eh_caixa"])
        self.assertTrue(contexto["pode_gerenciar_estoque"])
        self.assertTrue(contexto["pode_ver_relatorios"])

    def test_usuario_sem_grupo_nao_recebe_permissoes(self):
        usuario = User.objects.create_user(
            username="sem_grupo_contexto",
            password="senha_teste_123",
        )

        request = SimpleNamespace(user=usuario)

        contexto = perfil_usuario(request)

        self.assertFalse(contexto["eh_administrador"])
        self.assertFalse(contexto["eh_caixa"])
        self.assertFalse(contexto["pode_operar_vendas"])
        self.assertFalse(contexto["pode_consultar_estoque"])
        self.assertFalse(contexto["pode_gerenciar_estoque"])
        self.assertFalse(contexto["pode_ver_relatorios"])
