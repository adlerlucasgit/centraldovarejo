from django import forms

from produtos.models import Produto
from .models import Venda


class ItemCarrinhoForm(forms.Form):
    produto = forms.ModelChoiceField(
        queryset=Produto.objects.filter(
            ativo=True,
            estoque__current_stock__gt=0,
        ),
        label="Produto",
        empty_label="Selecione um produto",
    )

    quantidade = forms.IntegerField(
        min_value=1,
        label="Quantidade",
    )

class AtualizarQuantidadeForm(forms.Form):
    quantidade = forms.IntegerField(
        min_value=1,
        label="Nova quantidade",
    )


class FinalizarVendaForm(forms.Form):
    forma_pagamento = forms.ChoiceField(
        choices=[
            ("", "Selecione uma forma de pagamento"),
            *Venda.FormaPagamento.choices,
        ],
        label="Forma de pagamento",
        required=True,
    )
