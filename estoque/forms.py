from django import forms

from produtos.models import Produto


class EntradaEstoqueForm(forms.Form):
    produto = forms.ModelChoiceField(
        queryset=Produto.objects.filter(ativo=True),
        label="Produto",
        empty_label="Selecione um produto",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    quantity = forms.IntegerField(
        min_value=1,
        label="Quantidade de entrada",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Informe a quantidade",
                "min": 1,
            }
        ),
    )

    reason = forms.CharField(
        required=False,
        label="Observação",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Observação opcional sobre a entrada",
            }
        ),
    )


class AjusteEstoqueForm(forms.Form):
    produto = forms.ModelChoiceField(
        queryset=Produto.objects.filter(ativo=True),
        label="Produto",
        empty_label="Selecione um produto",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    current_stock = forms.IntegerField(
        min_value=0,
        label="Nova quantidade em estoque",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Informe a nova quantidade",
                "min": 0,
            }
        ),
    )

    reason = forms.CharField(
        required=True,
        min_length=3,
        label="Motivo do ajuste",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Descreva o motivo do ajuste",
            }
        ),
    )
