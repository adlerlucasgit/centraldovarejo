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


class CarrinhoVendaTests(TestCase):

    def setUp(self):
        self.usuario = User.objects.create_user(
            username="caixa_carrinho",
            password="senha_teste_123",
            is_superuser=True,
        )

        self.produto = Produto.objects.create(
            codigo="CARRINHO001",
            nome="Produto para Carrinho",
            preco=Decimal("25.00"),
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

    def test_acessar_tela_de_iniciar_venda(self):
        response = self.client.get(reverse("iniciar_venda"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "vendas/iniciar_venda.html")

    def test_adicionar_produto_ao_carrinho(self):
        response = self.client.post(
            reverse("iniciar_venda"),
            {
                "produto": self.produto.id,
                "quantidade": 2,
            },
        )

        self.assertRedirects(response, reverse("iniciar_venda"))

        carrinho = self.client.session["carrinho_venda"]

        self.assertEqual(carrinho[str(self.produto.id)], 2)

    def test_adicionar_mesmo_produto_soma_quantidades(self):
        self.preparar_carrinho(2)

        self.client.post(
            reverse("iniciar_venda"),
            {
                "produto": self.produto.id,
                "quantidade": 3,
            },
        )

        carrinho = self.client.session["carrinho_venda"]

        self.assertEqual(carrinho[str(self.produto.id)], 5)

    def test_bloquear_adicao_acima_do_estoque(self):
        response = self.client.post(
            reverse("iniciar_venda"),
            {
                "produto": self.produto.id,
                "quantidade": 11,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            "carrinho_venda",
            self.client.session,
        )

    def test_bloquear_adicao_com_quantidade_zero(self):
        response = self.client.post(
            reverse("iniciar_venda"),
            {
                "produto": self.produto.id,
                "quantidade": 0,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            "carrinho_venda",
            self.client.session,
        )

    def test_atualizar_quantidade_do_produto(self):
        self.preparar_carrinho(2)

        response = self.client.post(
            reverse(
                "atualizar_quantidade_venda",
                args=[self.produto.id],
            ),
            {"quantidade": 5},
        )

        self.assertRedirects(response, reverse("iniciar_venda"))

        carrinho = self.client.session["carrinho_venda"]

        self.assertEqual(carrinho[str(self.produto.id)], 5)

    def test_bloquear_atualizacao_com_quantidade_zero(self):
        self.preparar_carrinho(2)

        self.client.post(
            reverse(
                "atualizar_quantidade_venda",
                args=[self.produto.id],
            ),
            {"quantidade": 0},
        )

        carrinho = self.client.session["carrinho_venda"]

        self.assertEqual(carrinho[str(self.produto.id)], 2)

    def test_bloquear_atualizacao_acima_do_estoque(self):
        self.preparar_carrinho(2)

        self.client.post(
            reverse(
                "atualizar_quantidade_venda",
                args=[self.produto.id],
            ),
            {"quantidade": 11},
        )

        carrinho = self.client.session["carrinho_venda"]

        self.assertEqual(carrinho[str(self.produto.id)], 2)

    def test_remover_produto_do_carrinho(self):
        self.preparar_carrinho(2)

        response = self.client.post(
            reverse(
                "remover_produto_venda",
                args=[self.produto.id],
            )
        )

        self.assertRedirects(response, reverse("iniciar_venda"))

        carrinho = self.client.session.get("carrinho_venda", {})
        self.assertEqual(carrinho, {})

    def test_remover_produto_inexistente_nao_altera_carrinho(self):
        self.preparar_carrinho(2)

        response = self.client.post(
            reverse(
                "remover_produto_venda",
                args=[99999],
            )
        )

        self.assertRedirects(response, reverse("iniciar_venda"))

        carrinho = self.client.session["carrinho_venda"]

        self.assertEqual(carrinho[str(self.produto.id)], 2)

    def test_atualizar_quantidade_exige_post(self):
        self.preparar_carrinho(2)

        response = self.client.get(
            reverse(
                "atualizar_quantidade_venda",
                args=[self.produto.id],
            )
        )

        self.assertEqual(response.status_code, 405)

    def test_remover_produto_exige_post(self):
        self.preparar_carrinho(2)

        response = self.client.get(
            reverse(
                "remover_produto_venda",
                args=[self.produto.id],
            )
        )

        self.assertEqual(response.status_code, 405)

    def test_usuario_sem_permissao_nao_inicia_venda(self):
        usuario = User.objects.create_user(
            username="usuario_sem_permissao",
            password="senha_teste_123",
        )

        self.client.force_login(usuario)

        response = self.client.get(reverse("iniciar_venda"))

        self.assertEqual(response.status_code, 403)


class VendaAdminTests(TestCase):

    def setUp(self):
        self.usuario = User.objects.create_superuser(
            username="admin_vendas_teste",
            email="admin_vendas_teste@example.com",
            password="senha_teste_123",
        )

        self.produto = Produto.objects.create(
            codigo="ADMINVENDA001",
            nome="Produto para Teste do Admin",
            preco=Decimal("10.00"),
        )

        self.venda = Venda.objects.create(
            number="ADMIN-001",
            user=self.usuario,
            total=Decimal("20.00"),
            payment_method="PIX",
        )

        self.item = ItemVenda.objects.create(
            sale=self.venda,
            product=self.produto,
            quantity=2,
            unit_price=Decimal("10.00"),
            subtotal=Decimal("20.00"),
        )

        self.client.force_login(self.usuario)

    def test_bloquear_inclusao_de_venda(self):
        response = self.client.get(reverse("admin:vendas_venda_add"))

        self.assertEqual(response.status_code, 403)

    def test_bloquear_alteracao_de_venda(self):
        response = self.client.get(
            reverse(
                "admin:vendas_venda_change",
                args=[self.venda.id],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["has_change_permission"])
        self.assertTrue(response.context["has_view_permission"])

    def test_bloquear_exclusao_de_venda(self):
        response = self.client.get(
            reverse(
                "admin:vendas_venda_delete",
                args=[self.venda.id],
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_bloquear_inclusao_de_item(self):
        response = self.client.get(reverse("admin:vendas_itemvenda_add"))

        self.assertEqual(response.status_code, 403)

    def test_bloquear_alteracao_de_item(self):
        response = self.client.get(
            reverse(
                "admin:vendas_itemvenda_change",
                args=[self.item.id],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["has_change_permission"])
        self.assertTrue(response.context["has_view_permission"])

    def test_bloquear_exclusao_de_item(self):
        response = self.client.get(
            reverse(
                "admin:vendas_itemvenda_delete",
                args=[self.item.id],
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_permitir_consulta_de_vendas(self):
        response = self.client.get(reverse("admin:vendas_venda_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.venda.number)

    def test_permitir_consulta_de_itens(self):
        response = self.client.get(reverse("admin:vendas_itemvenda_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.produto.nome)
