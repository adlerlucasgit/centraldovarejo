from django import forms

from .models import Produto


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto

        fields = [
            "codigo",
            "nome",
            "preco",
        ]

        labels = {
            "codigo": "Código do produto",
            "nome": "Nome do produto",
            "preco": "Preço de venda",
        }

        widgets = {
            "codigo": forms.TextInput(
                attrs={
                    "placeholder": "Digite o código do produto",
                }
            ),
            "nome": forms.TextInput(
                attrs={
                    "placeholder": "Digite o nome do produto",
                }
            ),
            "preco": forms.NumberInput(
                attrs={
                    "placeholder": "0,00",
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
        }
