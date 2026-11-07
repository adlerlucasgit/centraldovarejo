from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from estoque.models import Estoque, MovimentacaoEstoque
from produtos.models import Produto
from .models import Venda, ItemVenda

User = get_user_model()


class FinalizarVendaTests(TestCase):

    def setUp(self):
        self.usuario = User.objects.create_user(
            username="teste_venda",
            password="senha_teste_123",
            is_superuser=True,
        )

        self.produto = Produto.objects.create(
            codigo="TESTEVENDA001",
            nome="Produto para Teste de Venda",
            preco=Decimal("15.90"),
        )

        self.estoque = Estoque.objects.get(produto=self.produto)
        self.estoque.current_stock = 10
        self.estoque.save()

        self.client.force_login(self.usuario)

    def preparar_carrinho(self, quantidade):
        session = self.client.session
        session["carrinho_venda"] = {
            str(self.produto.id): quantidade,
        }
        session.save()

    def test_finalizar_venda_com_sucesso(self):
        self.preparar_carrinho(2)

        response = self.client.post(
            reverse("finalizar_venda"),
            {"forma_pagamento": "PIX"},
        )

        self.assertRedirects(
            response,
            reverse("iniciar_venda"),
        )

        venda = Venda.objects.get()

        self.assertEqual(venda.user, self.usuario)
        self.assertEqual(venda.payment_method, "PIX")
        self.assertEqual(venda.total, Decimal("31.80"))

        item = ItemVenda.objects.get(sale=venda)

        self.assertEqual(item.product, self.produto)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.unit_price, Decimal("15.90"))
        self.assertEqual(item.subtotal, Decimal("31.80"))

        self.estoque.refresh_from_db()
        self.assertEqual(self.estoque.current_stock, 8)

        movimentacao = MovimentacaoEstoque.objects.get(
            tipo=MovimentacaoEstoque.Tipo.VENDA,
            produto=self.produto,
        )

        self.assertEqual(movimentacao.quantity, 2)
        self.assertEqual(movimentacao.user, self.usuario)

        self.assertNotIn("carrinho_venda", self.client.session)

    def test_bloquear_venda_com_estoque_insuficiente(self):
        self.preparar_carrinho(11)

        response = self.client.post(
            reverse("finalizar_venda"),
            {"forma_pagamento": "DINHEIRO"},
        )

        self.assertRedirects(
            response,
            reverse("iniciar_venda"),
        )

        self.assertEqual(Venda.objects.count(), 0)
        self.assertEqual(ItemVenda.objects.count(), 0)

        self.estoque.refresh_from_db()
        self.assertEqual(self.estoque.current_stock, 10)

        self.assertEqual(MovimentacaoEstoque.objects.count(), 0)
        self.assertIn("carrinho_venda", self.client.session)

    def test_bloquear_forma_de_pagamento_invalida(self):
        self.preparar_carrinho(1)

        response = self.client.post(
            reverse("finalizar_venda"),
            {"forma_pagamento": "BOLETO"},
        )

        self.assertRedirects(
            response,
            reverse("iniciar_venda"),
        )

        self.assertEqual(Venda.objects.count(), 0)

        self.estoque.refresh_from_db()
        self.assertEqual(self.estoque.current_stock, 10)

        self.assertIn("carrinho_venda", self.client.session)

    def test_bloquear_finalizacao_com_carrinho_vazio(self):
        response = self.client.post(
            reverse("finalizar_venda"),
            {"forma_pagamento": "PIX"},
        )

        self.assertRedirects(
            response,
            reverse("iniciar_venda"),
        )

        self.assertEqual(Venda.objects.count(), 0)
        self.assertEqual(ItemVenda.objects.count(), 0)

        self.estoque.refresh_from_db()
        self.assertEqual(self.estoque.current_stock, 10)
