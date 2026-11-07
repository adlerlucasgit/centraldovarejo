from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from produtos.models import Produto
from .models import Estoque, MovimentacaoEstoque

User = get_user_model()


class EstoqueTests(TestCase):

    def setUp(self):
        grupo_admin, _ = Group.objects.get_or_create(name="Administrador")

        grupo_caixa, _ = Group.objects.get_or_create(name="Caixa")

        self.admin = User.objects.create_user(
            username="admin_estoque",
            password="senha_teste_123",
        )
        self.admin.groups.add(grupo_admin)

        self.caixa = User.objects.create_user(
            username="caixa_estoque",
            password="senha_teste_123",
        )
        self.caixa.groups.add(grupo_caixa)

        self.outro_usuario = User.objects.create_user(
            username="outro_estoque",
            password="senha_teste_123",
        )

        self.produto = Produto.objects.create(
            codigo="EST001",
            nome="Produto Estoque",
            preco=Decimal("20.00"),
        )

        self.estoque = Estoque.objects.get(produto=self.produto)

        self.estoque.current_stock = 10
        self.estoque.save()

        self.client.force_login(self.admin)

    def test_registrar_entrada_com_sucesso(self):
        response = self.client.post(
            reverse("registrar_entrada"),
            {
                "produto": self.produto.id,
                "quantity": 5,
                "reason": "Reposição de mercadoria",
            },
        )

        self.assertRedirects(
            response,
            reverse("registrar_entrada"),
        )

        self.estoque.refresh_from_db()

        self.assertEqual(self.estoque.current_stock, 15)

        movimentacao = MovimentacaoEstoque.objects.get()

        self.assertEqual(
            movimentacao.tipo,
            MovimentacaoEstoque.Tipo.ENTRADA,
        )
        self.assertEqual(movimentacao.quantity, 5)
        self.assertEqual(movimentacao.user, self.admin)
        self.assertEqual(
            movimentacao.reason,
            "Reposição de mercadoria",
        )

    def test_bloquear_entrada_com_quantidade_zero(self):
        response = self.client.post(
            reverse("registrar_entrada"),
            {
                "produto": self.produto.id,
                "quantity": 0,
                "reason": "Teste inválido",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())

        self.estoque.refresh_from_db()

        self.assertEqual(self.estoque.current_stock, 10)
        self.assertEqual(MovimentacaoEstoque.objects.count(), 0)

    def test_bloquear_entrada_com_quantidade_negativa(self):
        response = self.client.post(
            reverse("registrar_entrada"),
            {
                "produto": self.produto.id,
                "quantity": -5,
                "reason": "Teste inválido",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())

        self.estoque.refresh_from_db()

        self.assertEqual(self.estoque.current_stock, 10)
        self.assertEqual(MovimentacaoEstoque.objects.count(), 0)

    def test_registrar_ajuste_com_aumento_de_estoque(self):
        response = self.client.post(
            reverse("registrar_ajuste"),
            {
                "produto": self.produto.id,
                "current_stock": 15,
                "reason": "Contagem física",
            },
        )

        self.assertRedirects(
            response,
            reverse("registrar_ajuste"),
        )

        self.estoque.refresh_from_db()

        self.assertEqual(self.estoque.current_stock, 15)

        movimentacao = MovimentacaoEstoque.objects.get()

        self.assertEqual(
            movimentacao.tipo,
            MovimentacaoEstoque.Tipo.AJUSTE,
        )
        self.assertEqual(movimentacao.quantity, 5)
        self.assertEqual(movimentacao.user, self.admin)
        self.assertIn("Saldo anterior: 10", movimentacao.reason)
        self.assertIn("Novo saldo: 15", movimentacao.reason)
        self.assertIn("Contagem física", movimentacao.reason)

    def test_registrar_ajuste_com_reducao_de_estoque(self):
        response = self.client.post(
            reverse("registrar_ajuste"),
            {
                "produto": self.produto.id,
                "current_stock": 6,
                "reason": "Correção de inventário",
            },
        )

        self.assertRedirects(
            response,
            reverse("registrar_ajuste"),
        )

        self.estoque.refresh_from_db()

        self.assertEqual(self.estoque.current_stock, 6)

        movimentacao = MovimentacaoEstoque.objects.get()

        self.assertEqual(
            movimentacao.tipo,
            MovimentacaoEstoque.Tipo.AJUSTE,
        )
        self.assertEqual(movimentacao.quantity, 4)

    def test_bloquear_ajuste_com_mesmo_saldo(self):
        response = self.client.post(
            reverse("registrar_ajuste"),
            {
                "produto": self.produto.id,
                "current_stock": 10,
                "reason": "Conferência de estoque",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].has_error("current_stock"))

        self.estoque.refresh_from_db()

        self.assertEqual(self.estoque.current_stock, 10)
        self.assertEqual(MovimentacaoEstoque.objects.count(), 0)

    def test_bloquear_ajuste_com_motivo_curto(self):
        response = self.client.post(
            reverse("registrar_ajuste"),
            {
                "produto": self.produto.id,
                "current_stock": 5,
                "reason": "AB",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())

        self.estoque.refresh_from_db()

        self.assertEqual(self.estoque.current_stock, 10)
        self.assertEqual(MovimentacaoEstoque.objects.count(), 0)

    def test_bloquear_ajuste_com_quantidade_negativa(self):
        response = self.client.post(
            reverse("registrar_ajuste"),
            {
                "produto": self.produto.id,
                "current_stock": -1,
                "reason": "Correção de inventário",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())

        self.estoque.refresh_from_db()

        self.assertEqual(self.estoque.current_stock, 10)
        self.assertEqual(MovimentacaoEstoque.objects.count(), 0)

    def test_consultar_estoque_como_administrador(self):
        response = self.client.get(reverse("consultar_estoque"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["estoques"]), 1)

    def test_consultar_estoque_como_caixa(self):
        self.client.force_login(self.caixa)

        response = self.client.get(reverse("consultar_estoque"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["estoques"]), 1)

    def test_filtrar_estoque_baixo(self):
        self.estoque.current_stock = 15
        self.estoque.save()

        response = self.client.get(
            reverse("consultar_estoque"),
            {"status": "baixo"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["status"], "baixo")
        self.assertEqual(len(response.context["estoques"]), 1)

    def test_filtrar_estoque_zerado(self):
        self.estoque.current_stock = 0
        self.estoque.save()

        response = self.client.get(
            reverse("consultar_estoque"),
            {"status": "sem_estoque"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["status"], "sem_estoque")
        self.assertEqual(len(response.context["estoques"]), 1)

    def test_nao_listar_produtos_inativos(self):
        self.produto.ativo = False
        self.produto.save()

        response = self.client.get(reverse("consultar_estoque"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["estoques"]), 0)

    def test_caixa_nao_pode_registrar_entrada(self):
        self.client.force_login(self.caixa)

        response = self.client.get(reverse("registrar_entrada"))

        self.assertEqual(response.status_code, 403)

    def test_caixa_nao_pode_registrar_ajuste(self):
        self.client.force_login(self.caixa)

        response = self.client.get(reverse("registrar_ajuste"))

        self.assertEqual(response.status_code, 403)

    def test_caixa_nao_pode_acessar_historico(self):
        self.client.force_login(self.caixa)

        response = self.client.get(reverse("historico_movimentacoes"))

        self.assertEqual(response.status_code, 403)

    def test_usuario_sem_grupo_nao_pode_consultar_estoque(self):
        self.client.force_login(self.outro_usuario)

        response = self.client.get(reverse("consultar_estoque"))

        self.assertEqual(response.status_code, 403)

    def test_usuario_nao_autenticado_nao_acessa_estoque(self):
        self.client.logout()

        response = self.client.get(reverse("consultar_estoque"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)
