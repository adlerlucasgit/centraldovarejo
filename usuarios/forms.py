from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from produtos.permissoes import configurar_permissoes_grupo_produtos

User = get_user_model()


class UsuarioCriacaoForm(UserCreationForm):
    first_name = forms.CharField(
        label="Nome",
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={"placeholder": "Digite o nome"}
        ),
    )

    last_name = forms.CharField(
        label="Sobrenome",
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={"placeholder": "Digite o sobrenome"}
        ),
    )

    email = forms.EmailField(
        label="E-mail",
        required=True,
        widget=forms.EmailInput(
            attrs={"placeholder": "Digite o e-mail"}
        ),
    )

    perfil = forms.ChoiceField(
        label="Perfil de acesso",
        choices=[
            ("Administrador", "Administrador"),
            ("Caixa", "Caixa"),
        ],
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "perfil",
        )

        labels = {
            "username": "Nome de usuário",
        }

        widgets = {
            "username": forms.TextInput(
                attrs={"placeholder": "Digite o nome de usuário"}
            ),
        }

    def save(self, commit=True):
        usuario = super().save(commit=commit)

        if commit:
            grupo, _ = Group.objects.get_or_create(
                name=self.cleaned_data["perfil"]
            )

            configurar_permissoes_grupo_produtos(grupo)
            usuario.groups.set([grupo])

        return usuario


class UsuarioEdicaoForm(forms.ModelForm):
    perfil = forms.ChoiceField(
        label="Perfil de acesso",
        choices=[
            ("Administrador", "Administrador"),
            ("Caixa", "Caixa"),
        ],
    )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
        ]

        labels = {
            "username": "Nome de usuário",
            "first_name": "Nome",
            "last_name": "Sobrenome",
            "email": "E-mail",
            "is_active": "Usuário ativo",
        }

        widgets = {
            "username": forms.TextInput(
                attrs={"placeholder": "Digite o nome de usuário"}
            ),
            "first_name": forms.TextInput(
                attrs={"placeholder": "Digite o nome"}
            ),
            "last_name": forms.TextInput(
                attrs={"placeholder": "Digite o sobrenome"}
            ),
            "email": forms.EmailInput(
                attrs={"placeholder": "Digite o e-mail"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.is_superuser:
            self.fields["perfil"].initial = "Administrador"
        else:
            grupo = self.instance.groups.filter(
                name__in=["Administrador", "Caixa"]
            ).first()

            if grupo:
                self.fields["perfil"].initial = grupo.name

    def save(self, commit=True):
        usuario = super().save(commit=commit)

        if commit:
            grupo, _ = Group.objects.get_or_create(name=self.cleaned_data["perfil"])

            configurar_permissoes_grupo_produtos(grupo)
            usuario.groups.set([grupo])

        return usuario


for form_class in [UsuarioCriacaoForm, UsuarioEdicaoForm]:
    for field in form_class.base_fields.values():
        field.widget.attrs.setdefault("class", "form-control")

UsuarioCriacaoForm.base_fields["perfil"].widget.attrs["class"] = "form-select"
UsuarioEdicaoForm.base_fields["perfil"].widget.attrs["class"] = "form-select"
