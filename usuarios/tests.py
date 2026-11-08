from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class GerenciamentoUsuariosTests(TestCase):

    def setUp(self):
        self.grupo_admin, _ = Group.objects.get_or_create(name="Administrador")
        self.grupo_caixa, _ = Group.objects.get_or_create(name="Caixa")

        self.admin = User.objects.create_superuser(
            username="admin_teste",
            email="admin@teste.com",
            password="SenhaForte@2026",
        )

        self.caixa = User.objects.create_user(
            username="caixa_teste",
            email="caixa@teste.com",
            password="SenhaForte@2026",
        )
        self.caixa.groups.add(self.grupo_caixa)

        self.client.force_login(self.admin)

    def criar_dados_usuario(self, **alteracoes):
        dados = {
            "username": "novo_usuario",
            "first_name": "Novo",
            "last_name": "Usuario",
            "email": "novo@teste.com",
            "password1": "SenhaForte@2026",
            "password2": "SenhaForte@2026",
            "perfil": "Caixa",
        }
        dados.update(alteracoes)
        return dados

    def test_listar_usuarios(self):
        resposta = self.client.get(reverse("listar_usuarios"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "caixa_teste")

    def test_pesquisar_usuarios(self):
        resposta = self.client.get(
            reverse("listar_usuarios"),
            {"busca": "caixa_teste"},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "caixa_teste")

    def test_filtrar_usuarios_ativos(self):
        resposta = self.client.get(
            reverse("listar_usuarios"),
            {"status": "ativos"},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "admin_teste")

    def test_cadastrar_usuario_caixa(self):
        resposta = self.client.post(
            reverse("cadastrar_usuario"),
            self.criar_dados_usuario(),
        )

        self.assertRedirects(resposta, reverse("listar_usuarios"))

        usuario = User.objects.get(username="novo_usuario")

        self.assertEqual(usuario.first_name, "Novo")
        self.assertTrue(usuario.groups.filter(name="Caixa").exists())
        self.assertTrue(usuario.is_active)

    def test_cadastrar_usuario_administrador(self):
        resposta = self.client.post(
            reverse("cadastrar_usuario"),
            self.criar_dados_usuario(
                username="novo_admin",
                perfil="Administrador",
            ),
        )

        self.assertRedirects(resposta, reverse("listar_usuarios"))

        usuario = User.objects.get(username="novo_admin")

        self.assertTrue(usuario.groups.filter(name="Administrador").exists())

    def test_editar_usuario(self):
        resposta = self.client.post(
            reverse("editar_usuario", args=[self.caixa.id]),
            {
                "username": "caixa_teste",
                "first_name": "Caixa",
                "last_name": "Atualizado",
                "email": "caixa@teste.com",
                "is_active": "on",
                "perfil": "Caixa",
            },
        )

        self.assertRedirects(resposta, reverse("listar_usuarios"))

        self.caixa.refresh_from_db()

        self.assertEqual(self.caixa.last_name, "Atualizado")
        self.assertTrue(self.caixa.groups.filter(name="Caixa").exists())

    def test_suspender_usuario(self):
        resposta = self.client.post(reverse("suspender_usuario", args=[self.caixa.id]))

        self.assertRedirects(resposta, reverse("listar_usuarios"))

        self.caixa.refresh_from_db()
        self.assertFalse(self.caixa.is_active)

    def test_reativar_usuario(self):
        self.caixa.is_active = False
        self.caixa.save(update_fields=["is_active"])

        resposta = self.client.post(reverse("reativar_usuario", args=[self.caixa.id]))

        self.assertRedirects(resposta, reverse("listar_usuarios"))

        self.caixa.refresh_from_db()
        self.assertTrue(self.caixa.is_active)

    def test_excluir_usuario(self):
        resposta = self.client.post(reverse("excluir_usuario", args=[self.caixa.id]))

        self.assertRedirects(resposta, reverse("listar_usuarios"))
        self.assertFalse(User.objects.filter(id=self.caixa.id).exists())

    def test_administrador_nao_pode_suspender_a_propria_conta(self):
        resposta = self.client.post(reverse("suspender_usuario", args=[self.admin.id]))

        self.assertRedirects(resposta, reverse("listar_usuarios"))

        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_administrador_nao_pode_excluir_a_propria_conta(self):
        resposta = self.client.post(reverse("excluir_usuario", args=[self.admin.id]))

        self.assertRedirects(resposta, reverse("listar_usuarios"))
        self.assertTrue(User.objects.filter(id=self.admin.id).exists())

    def test_caixa_nao_pode_acessar_listagem(self):
        self.client.force_login(self.caixa)

        resposta = self.client.get(reverse("listar_usuarios"))

        self.assertEqual(resposta.status_code, 403)

    def test_caixa_nao_pode_cadastrar_usuario(self):
        self.client.force_login(self.caixa)

        resposta = self.client.get(reverse("cadastrar_usuario"))

        self.assertEqual(resposta.status_code, 403)

    def test_usuario_nao_autenticado_e_redirecionado(self):
        self.client.logout()

        resposta = self.client.get(reverse("listar_usuarios"))

        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/login/", resposta.url)
