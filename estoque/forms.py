from django import forms

from produtos.models import Produto


class EntradaEstoqueForm(forms.Form):
    produto = forms.ModelChoiceField(
        queryset=Produto.objects.filter(ativo=True),
        label="Produto",
        empty_label="Selecione um produto",
    )

    quantity = forms.IntegerField(
        min_value=1,
        label="Quantidade de entrada",
    )

    reason = forms.CharField(
        required=False,
        label="Observação",
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class AjusteEstoqueForm(forms.Form):
    produto = forms.ModelChoiceField(
        queryset=Produto.objects.filter(ativo=True),
        label="Produto",
        empty_label="Selecione um produto",
    )

    current_stock = forms.IntegerField(
        min_value=0,
        label="Nova quantidade em estoque",
    )

    reason = forms.CharField(
        required=True,
        min_length=3,
        label="Motivo do ajuste",
        widget=forms.Textarea(attrs={"rows": 3}),
    )
