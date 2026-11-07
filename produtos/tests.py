from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from estoque.models import Estoque
from .models import Produto

User = get_user_model()


class ProdutoTests(TestCase):

    def setUp(self):
        self.usuario = User.objects.create_user(
            username="usuario_produto",
            password="senha_teste_123",
        )

        permissoes = Permission.objects.filter(
            content_type__app_label="produtos",
            codename__in=[
                "view_produto",
                "add_produto",
                "change_produto",
            ],
        )

        self.usuario.user_permissions.add(*permissoes)

        self.client.force_login(self.usuario)

    def criar_produto(self, codigo="PROD001", nome="Produto Teste"):
        return Produto.objects.create(
            codigo=codigo,
            nome=nome,
            preco=Decimal("25.90"),
        )

    def test_cadastrar_produto_com_sucesso(self):
        response = self.client.post(
            reverse("cadastrar_produto"),
            {
                "codigo": "PROD002",
                "nome": "Produto Novo",
                "preco": "35.50",
            },
        )

        self.assertRedirects(
            response,
            reverse("listar_produtos"),
        )

        produto = Produto.objects.get(codigo="PROD002")

        self.assertEqual(produto.nome, "Produto Novo")
        self.assertEqual(produto.preco, Decimal("35.50"))
        self.assertTrue(produto.ativo)

    def test_cadastrar_produto_cria_estoque_automaticamente(self):
        response = self.client.post(
            reverse("cadastrar_produto"),
            {
                "codigo": "PROD003",
                "nome": "Produto com Estoque",
                "preco": "10.00",
            },
        )

        self.assertRedirects(
            response,
            reverse("listar_produtos"),
        )

        produto = Produto.objects.get(codigo="PROD003")
        estoque = Estoque.objects.get(produto=produto)

        self.assertEqual(estoque.current_stock, 0)

    def test_bloquear_cadastro_com_codigo_duplicado(self):
        self.criar_produto(codigo="DUPLICADO")

        response = self.client.post(
            reverse("cadastrar_produto"),
            {
                "codigo": "DUPLICADO",
                "nome": "Outro Produto",
                "preco": "20.00",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())
        self.assertEqual(Produto.objects.count(), 1)

    def test_bloquear_cadastro_com_preco_zero(self):
        response = self.client.post(
            reverse("cadastrar_produto"),
            {
                "codigo": "PROD004",
                "nome": "Produto Inválido",
                "preco": "0.00",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())
        self.assertFalse(Produto.objects.filter(codigo="PROD004").exists())

    def test_bloquear_cadastro_com_preco_negativo(self):
        response = self.client.post(
            reverse("cadastrar_produto"),
            {
                "codigo": "PROD005",
                "nome": "Produto Inválido",
                "preco": "-10.00",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())
        self.assertFalse(Produto.objects.filter(codigo="PROD005").exists())

    def test_listar_somente_produtos_ativos(self):
        produto_ativo = self.criar_produto()
        produto_inativo = self.criar_produto(
            codigo="PROD006",
            nome="Produto Inativo",
        )

        produto_inativo.ativo = False
        produto_inativo.save()

        response = self.client.get(reverse("listar_produtos"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, produto_ativo.nome)
        self.assertNotContains(response, produto_inativo.nome)

    def test_editar_produto_com_sucesso(self):
        produto = self.criar_produto()

        response = self.client.post(
            reverse("editar_produto", args=[produto.id]),
            {
                "codigo": produto.codigo,
                "nome": "Produto Editado",
                "preco": "45.00",
            },
        )

        self.assertRedirects(
            response,
            reverse("listar_produtos"),
        )

        produto.refresh_from_db()

        self.assertEqual(produto.nome, "Produto Editado")
        self.assertEqual(produto.preco, Decimal("45.00"))

    def test_desativar_produto_com_sucesso(self):
        produto = self.criar_produto()

        response = self.client.post(reverse("desativar_produto", args=[produto.id]))

        self.assertRedirects(
            response,
            reverse("listar_produtos"),
        )

        produto.refresh_from_db()

        self.assertFalse(produto.ativo)

    def test_bloquear_desativacao_por_get(self):
        produto = self.criar_produto()

        response = self.client.get(reverse("desativar_produto", args=[produto.id]))

        self.assertEqual(response.status_code, 405)

        produto.refresh_from_db()

        self.assertTrue(produto.ativo)

    def test_usuario_sem_permissao_nao_acessa_produtos(self):
        usuario_sem_permissao = User.objects.create_user(
            username="sem_permissao",
            password="senha_teste_123",
        )

        self.client.force_login(usuario_sem_permissao)

        rotas = [
            reverse("listar_produtos"),
            reverse("cadastrar_produto"),
            reverse("editar_produto", args=[1]),
            reverse("desativar_produto", args=[1]),
        ]

        for rota in rotas:
            with self.subTest(rota=rota):
                response = self.client.get(rota)

                self.assertEqual(response.status_code, 403)

    def test_usuario_nao_autenticado_e_redirecionado(self):
        self.client.logout()

        response = self.client.get(reverse("listar_produtos"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)
