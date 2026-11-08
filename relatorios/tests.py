from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils import timezone

from estoque.models import Estoque
from produtos.models import Produto
from vendas.models import Venda, ItemVenda

User = get_user_model()


class RelatorioGeralTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        grupo_admin = Group.objects.create(name="Administrador")
        grupo_caixa = Group.objects.create(name="Caixa")

        cls.admin = User.objects.create_user(
            username="admin_relatorio",
            password="senha123",
        )
        cls.admin.groups.add(grupo_admin)

        cls.caixa = User.objects.create_user(
            username="caixa_relatorio",
            password="senha123",
        )
        cls.caixa.groups.add(grupo_caixa)

        cls.produto1 = Produto.objects.create(
            codigo="REL001",
            nome="Produto A",
            preco=Decimal("20.00"),
        )

        cls.produto2 = Produto.objects.create(
            codigo="REL002",
            nome="Produto B",
            preco=Decimal("30.00"),
        )

        Estoque.objects.filter(produto=cls.produto1).update(current_stock=10)

        Estoque.objects.filter(produto=cls.produto2).update(current_stock=0)

        cls.venda1 = cls.criar_venda(
            numero="REL-VENDA-001",
            total=Decimal("100.00"),
            pagamento=Venda.FormaPagamento.PIX,
            dia=5,
        )

        cls.venda2 = cls.criar_venda(
            numero="REL-VENDA-002",
            total=Decimal("50.00"),
            pagamento=Venda.FormaPagamento.PIX,
            dia=6,
        )

        cls.venda3 = cls.criar_venda(
            numero="REL-VENDA-003",
            total=Decimal("30.00"),
            pagamento=Venda.FormaPagamento.DINHEIRO,
            dia=6,
        )

        cls.venda_fora_periodo = cls.criar_venda(
            numero="REL-VENDA-004",
            total=Decimal("900.00"),
            pagamento=Venda.FormaPagamento.CARTAO,
            dia=31,
            mes=10,
        )

        ItemVenda.objects.create(
            sale=cls.venda1,
            product=cls.produto1,
            quantity=2,
            unit_price=Decimal("20.00"),
            subtotal=Decimal("40.00"),
        )

        ItemVenda.objects.create(
            sale=cls.venda1,
            product=cls.produto2,
            quantity=1,
            unit_price=Decimal("30.00"),
            subtotal=Decimal("30.00"),
        )

        ItemVenda.objects.create(
            sale=cls.venda2,
            product=cls.produto1,
            quantity=3,
            unit_price=Decimal("20.00"),
            subtotal=Decimal("60.00"),
        )

        ItemVenda.objects.create(
            sale=cls.venda3,
            product=cls.produto2,
            quantity=1,
            unit_price=Decimal("30.00"),
            subtotal=Decimal("30.00"),
        )

        ItemVenda.objects.create(
            sale=cls.venda_fora_periodo,
            product=cls.produto2,
            quantity=10,
            unit_price=Decimal("30.00"),
            subtotal=Decimal("300.00"),
        )

    @classmethod
    def criar_venda(
        cls,
        numero,
        total,
        pagamento,
        dia,
        mes=11,
    ):
        venda = Venda.objects.create(
            number=numero,
            user=cls.admin,
            total=total,
            payment_method=pagamento,
        )

        data_venda = timezone.make_aware(datetime(2026, mes, dia, 12, 0))

        Venda.objects.filter(pk=venda.pk).update(date_time=data_venda)

        return venda

    def acessar_relatorio(self):
        self.client.force_login(self.admin)

        return self.client.get(
            "/relatorios/",
            {
                "data_inicial": "2026-11-01",
                "data_final": "2026-11-30",
            },
        )

    def test_administrador_acessa_relatorios(self):
        response = self.acessar_relatorio()

        self.assertEqual(response.status_code, 200)

    def test_caixa_nao_acessa_relatorios(self):
        self.client.force_login(self.caixa)

        response = self.client.get("/relatorios/")

        self.assertEqual(response.status_code, 403)

    def test_usuario_nao_autenticado_e_redirecionado(self):
        response = self.client.get("/relatorios/")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_calculos_do_relatorio(self):
        response = self.acessar_relatorio()

        self.assertEqual(response.context["numero_vendas"], 3)

        self.assertEqual(
            response.context["valor_total"],
            Decimal("180.00"),
        )

        self.assertEqual(
            response.context["produtos_vendidos"],
            7,
        )

        self.assertEqual(
            response.context["ticket_medio"],
            Decimal("60.00"),
        )

        self.assertEqual(
            response.context["total_produtos_cadastrados"],
            2,
        )

        self.assertEqual(response.context["estoque_baixo"], 1)
        self.assertEqual(response.context["estoque_zerado"], 1)

    def test_produtos_mais_vendidos(self):
        response = self.acessar_relatorio()

        produtos = response.context["produtos_mais_vendidos"]

        self.assertEqual(len(produtos), 2)

        self.assertEqual(
            produtos[0]["product__nome"],
            "Produto A",
        )

        self.assertEqual(
            produtos[0]["quantidade_vendida"],
            5,
        )

    def test_forma_de_pagamento_mais_utilizada(self):
        response = self.acessar_relatorio()

        pagamento = response.context["forma_pagamento_mais_utilizada"]

        self.assertEqual(
            pagamento["payment_method"],
            Venda.FormaPagamento.PIX,
        )

        self.assertEqual(pagamento["quantidade"], 2)
        self.assertEqual(pagamento["nome"], "PIX")

        pagamentos = response.context["pagamentos"]
        nomes_pagamentos = {item["nome"] for item in pagamentos}

        self.assertIn("Dinheiro", nomes_pagamentos)
        self.assertIn("PIX", nomes_pagamentos)

    def test_vendas_fora_do_periodo_nao_sao_contabilizadas(self):
        response = self.acessar_relatorio()

        self.assertEqual(response.context["numero_vendas"], 3)

        self.assertNotEqual(
            response.context["valor_total"],
            Decimal("1080.00"),
        )

    def test_periodo_invertido_apresenta_erro(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            "/relatorios/",
            {
                "data_inicial": "2026-11-30",
                "data_final": "2026-11-01",
            },
        )

        self.assertEqual(response.status_code, 200)

        formulario = response.context["formulario"]

        self.assertFalse(formulario.is_valid())

        self.assertIn(
            "A data inicial não pode ser posterior à data final.",
            formulario.non_field_errors(),
        )
