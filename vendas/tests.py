from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

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


class HistoricoVendasTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_historico",
            password="senha_teste_123",
            is_superuser=True,
        )

        grupo_caixa = Group.objects.create(name="Caixa")

        self.caixa = User.objects.create_user(
            username="caixa_historico",
            password="senha_teste_123",
        )
        self.caixa.groups.add(grupo_caixa)

        self.outro_caixa = User.objects.create_user(
            username="outro_caixa",
            password="senha_teste_123",
        )
        self.outro_caixa.groups.add(grupo_caixa)

        self.venda_admin = Venda.objects.create(
            number="HIST-001",
            user=self.admin,
            total=Decimal("50.00"),
            payment_method="DINHEIRO",
        )

        self.venda_caixa = Venda.objects.create(
            number="HIST-002",
            user=self.caixa,
            total=Decimal("30.00"),
            payment_method="PIX",
        )

        self.venda_outro_caixa = Venda.objects.create(
            number="HIST-003",
            user=self.outro_caixa,
            total=Decimal("20.00"),
            payment_method="CARTAO",
        )

        self.produto = Produto.objects.create(
            codigo="HISTPROD001",
            nome="Produto para Histórico",
            preco=Decimal("10.00"),
        )

        ItemVenda.objects.create(
            sale=self.venda_caixa,
            product=self.produto,
            quantity=3,
            unit_price=Decimal("10.00"),
            subtotal=Decimal("30.00"),
        )

    def test_administrador_visualiza_todas_as_vendas(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("historico_vendas"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["vendas"]), 3)

    def test_caixa_visualiza_somente_suas_vendas(self):
        self.client.force_login(self.caixa)

        response = self.client.get(reverse("historico_vendas"))

        self.assertEqual(response.status_code, 200)

        vendas = list(response.context["vendas"])

        self.assertEqual(len(vendas), 1)
        self.assertEqual(vendas[0], self.venda_caixa)

    def test_caixa_nao_acessa_detalhes_de_outra_venda(self):
        self.client.force_login(self.caixa)

        response = self.client.get(
            reverse(
                "detalhes_venda",
                args=[self.venda_admin.id],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_caixa_acessa_detalhes_de_sua_propria_venda(self):
        self.client.force_login(self.caixa)

        response = self.client.get(
            reverse(
                "detalhes_venda",
                args=[self.venda_caixa.id],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["venda"],
            self.venda_caixa,
        )
        self.assertEqual(len(response.context["itens"]), 1)


class FiltroHistoricoVendasTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_filtros",
            password="senha_teste_123",
            is_superuser=True,
        )

        grupo_caixa = Group.objects.create(name="Caixa")

        self.caixa = User.objects.create_user(
            username="caixa_filtros",
            password="senha_teste_123",
        )
        self.caixa.groups.add(grupo_caixa)

        self.outro_caixa = User.objects.create_user(
            username="outro_filtros",
            password="senha_teste_123",
        )
        self.outro_caixa.groups.add(grupo_caixa)

        self.hoje = timezone.localdate()

        self.venda1 = Venda.objects.create(
            number="FILTRO-001",
            user=self.caixa,
            total=Decimal("50.00"),
            payment_method="DINHEIRO",
        )

        self.venda2 = Venda.objects.create(
            number="FILTRO-002",
            user=self.caixa,
            total=Decimal("30.00"),
            payment_method="PIX",
        )

        self.venda3 = Venda.objects.create(
            number="FILTRO-003",
            user=self.outro_caixa,
            total=Decimal("20.00"),
            payment_method="CARTAO",
        )

        Venda.objects.filter(id=self.venda1.id).update(
            date_time=timezone.now() - timedelta(days=2)
        )

        Venda.objects.filter(id=self.venda2.id).update(
            date_time=timezone.now() - timedelta(days=1)
        )

        Venda.objects.filter(id=self.venda3.id).update(date_time=timezone.now())

        self.client.force_login(self.admin)

    def test_filtrar_por_data_inicial_e_final(self):
        response = self.client.get(
            reverse("historico_vendas"),
            {
                "data_inicial": (self.hoje - timedelta(days=1)).isoformat(),
                "data_final": self.hoje.isoformat(),
            },
        )

        vendas = list(response.context["vendas"])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(vendas), 2)
        self.assertNotIn(self.venda1, vendas)

    def test_filtrar_por_operador(self):
        response = self.client.get(
            reverse("historico_vendas"),
            {"operador": self.caixa.id},
        )

        vendas = list(response.context["vendas"])

        self.assertEqual(len(vendas), 2)
        self.assertIn(self.venda1, vendas)
        self.assertIn(self.venda2, vendas)
        self.assertNotIn(self.venda3, vendas)

    def test_filtrar_por_forma_de_pagamento(self):
        response = self.client.get(
            reverse("historico_vendas"),
            {"forma_pagamento": "PIX"},
        )

        vendas = list(response.context["vendas"])

        self.assertEqual(len(vendas), 1)
        self.assertEqual(vendas[0], self.venda2)

    def test_pesquisar_por_parte_do_numero(self):
        response = self.client.get(
            reverse("historico_vendas"),
            {"numero": "FILTRO-00"},
        )

        vendas = list(response.context["vendas"])

        self.assertEqual(len(vendas), 3)

    def test_combinar_filtros(self):
        response = self.client.get(
            reverse("historico_vendas"),
            {
                "operador": self.caixa.id,
                "forma_pagamento": "PIX",
            },
        )

        vendas = list(response.context["vendas"])

        self.assertEqual(len(vendas), 1)
        self.assertEqual(vendas[0], self.venda2)

    def test_rejeitar_periodo_com_datas_invertidas(self):
        response = self.client.get(
            reverse("historico_vendas"),
            {
                "data_inicial": self.hoje.isoformat(),
                "data_final": (self.hoje - timedelta(days=1)).isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].has_error("data_final"))
        self.assertEqual(len(response.context["vendas"]), 3)
