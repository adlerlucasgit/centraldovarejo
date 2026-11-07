from django import forms
from django.contrib.auth import get_user_model
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


class FiltroHistoricoVendasForm(forms.Form):
    data_inicial = forms.DateField(
        required=False,
        label="Data inicial",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    data_final = forms.DateField(
        required=False,
        label="Data final",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    operador = forms.ModelChoiceField(
        queryset=get_user_model()
        .objects.filter(
            vendas__isnull=False,
        )
        .distinct()
        .order_by("username"),
        required=False,
        label="Operador",
        empty_label="Todos os operadores",
    )

    forma_pagamento = forms.ChoiceField(
        choices=[
            ("", "Todas as formas de pagamento"),
            *Venda.FormaPagamento.choices,
        ],
        required=False,
        label="Forma de pagamento",
    )

    numero = forms.CharField(
        required=False,
        max_length=30,
        label="Número da venda",
    )

    def clean(self):
        dados = super().clean()

        data_inicial = dados.get("data_inicial")
        data_final = dados.get("data_final")

        if data_inicial and data_final and data_inicial > data_final:
            self.add_error(
                "data_final",
                "A data final não pode ser anterior à data inicial.",
            )

        return dados
