from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from produtos.models import Produto
from .forms import ItemCarrinhoForm


def eh_operador_venda(user):
    return (
        user.is_superuser
        or user.groups.filter(name__in=["Administrador", "Caixa"]).exists()
    )


@login_required
def iniciar_venda(request):
    if not eh_operador_venda(request.user):
        raise PermissionDenied

    carrinho = request.session.get("carrinho_venda", {})

    if request.method == "POST":
        form = ItemCarrinhoForm(request.POST)

        if form.is_valid():
            produto = form.cleaned_data["produto"]
            quantidade = form.cleaned_data["quantidade"]

            estoque = produto.estoque
            quantidade_atual = int(carrinho.get(str(produto.id), 0))

            quantidade_total = quantidade_atual + quantidade

            if quantidade_total > estoque.current_stock:
                form.add_error(
                    "quantidade",
                    (
                        f"Estoque insuficiente. "
                        f"Disponível: {estoque.current_stock}. "
                        f"Já existem {quantidade_atual} "
                        "unidades desse produto no carrinho."
                    ),
                )
            else:
                carrinho[str(produto.id)] = quantidade_total
                request.session["carrinho_venda"] = carrinho

                return redirect("iniciar_venda")
    else:
        form = ItemCarrinhoForm()

    produtos = Produto.objects.filter(
        id__in=carrinho.keys(),
        ativo=True,
    ).select_related("estoque")

    itens_carrinho = []
    total_carrinho = 0

    for produto in produtos:
        quantidade = int(carrinho[str(produto.id)])
        subtotal = produto.preco * quantidade

        itens_carrinho.append(
            {
                "produto": produto,
                "quantidade": quantidade,
                "subtotal": subtotal,
            }
        )

        total_carrinho += subtotal

    return render(
        request,
        "vendas/iniciar_venda.html",
        {
            "form": form,
            "itens_carrinho": itens_carrinho,
            "total_carrinho": total_carrinho,
        },
    )
