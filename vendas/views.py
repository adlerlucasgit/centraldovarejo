from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from produtos.models import Produto
from .models import Venda

from .forms import (
    ItemCarrinhoForm,
    AtualizarQuantidadeForm,
    FinalizarVendaForm,
    FiltroHistoricoVendasForm,
)

from .services import finalizar_venda as executar_finalizacao

def eh_operador_venda(user):
    return (
        user.is_superuser
        or user.groups.filter(name__in=["Administrador", "Caixa"]).exists()
    )


def vendas_visiveis_para(user):
    vendas = Venda.objects.select_related("user")

    if user.is_superuser or user.groups.filter(name="Administrador").exists():
        return vendas

    if user.groups.filter(name="Caixa").exists():
        return vendas.filter(user=user)

    raise PermissionDenied


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
            "finalizar_form": FinalizarVendaForm(),
            "itens_carrinho": itens_carrinho,
            "total_carrinho": total_carrinho,
        },
    )

@login_required
@require_POST
def atualizar_quantidade(request, produto_id):
    if not eh_operador_venda(request.user):
        raise PermissionDenied

    carrinho = request.session.get("carrinho_venda", {})
    chave_produto = str(produto_id)

    if chave_produto not in carrinho:
        messages.error(request, "Produto não encontrado no carrinho.")
        return redirect("iniciar_venda")

    form = AtualizarQuantidadeForm(request.POST)

    if not form.is_valid():
        messages.error(request, "Informe uma quantidade válida.")
        return redirect("iniciar_venda")

    produto = get_object_or_404(
        Produto.objects.select_related("estoque"),
        id=produto_id,
        ativo=True,
    )

    quantidade = form.cleaned_data["quantidade"]
    estoque = produto.estoque

    if quantidade > estoque.current_stock:
        messages.error(
            request,
            (
                f"Estoque insuficiente para {produto.nome}. "
                f"Disponível: {estoque.current_stock}."
            ),
        )
        return redirect("iniciar_venda")

    carrinho[chave_produto] = quantidade
    request.session["carrinho_venda"] = carrinho

    messages.success(request, "Quantidade atualizada com sucesso.")

    return redirect("iniciar_venda")

@login_required
@require_POST
def remover_produto(request, produto_id):
    if not eh_operador_venda(request.user):
        raise PermissionDenied

    carrinho = request.session.get("carrinho_venda", {})
    chave_produto = str(produto_id)

    if chave_produto in carrinho:
        del carrinho[chave_produto]
        request.session["carrinho_venda"] = carrinho

        messages.success(request, "Produto removido do carrinho.")
    else:
        messages.error(request, "Produto não encontrado no carrinho.")

    return redirect("iniciar_venda")

@login_required
@require_POST
def finalizar_venda(request):
    if not eh_operador_venda(request.user):
        raise PermissionDenied

    carrinho = request.session.get("carrinho_venda", {})

    if not carrinho:
        messages.error(
            request, "Não é possível finalizar uma venda com o carrinho vazio."
        )
        return redirect("iniciar_venda")

    form = FinalizarVendaForm(request.POST)

    if not form.is_valid():
        messages.error(request, "Selecione uma forma de pagamento válida.")
        return redirect("iniciar_venda")

    itens = [
        {
            "produto_id": produto_id,
            "quantidade": quantidade,
        }
        for produto_id, quantidade in carrinho.items()
    ]

    try:
        venda = executar_finalizacao(
            user=request.user,
            itens=itens,
            payment_method=form.cleaned_data["forma_pagamento"],
        )
    except ValidationError as erro:
        messages.error(request, " ".join(erro.messages))
        return redirect("iniciar_venda")

    request.session.pop("carrinho_venda", None)

    messages.success(
        request,
        (
            f"Venda {venda.number} finalizada com sucesso! "
            f"Total: R$ {venda.total:.2f}."
        ),
    )

    return redirect("iniciar_venda")


@login_required
def historico_vendas(request):
    vendas = vendas_visiveis_para(request.user)

    form = FiltroHistoricoVendasForm(request.GET or None)

    if form.is_valid():
        data_inicial = form.cleaned_data.get("data_inicial")
        data_final = form.cleaned_data.get("data_final")
        operador = form.cleaned_data.get("operador")
        forma_pagamento = form.cleaned_data.get("forma_pagamento")
        numero = form.cleaned_data.get("numero")

        if data_inicial:
            vendas = vendas.filter(date_time__date__gte=data_inicial)

        if data_final:
            vendas = vendas.filter(date_time__date__lte=data_final)

        if operador:
            vendas = vendas.filter(user=operador)

        if forma_pagamento:
            vendas = vendas.filter(payment_method=forma_pagamento)

        if numero:
            vendas = vendas.filter(number__icontains=numero)

    return render(
        request,
        "vendas/historico_vendas.html",
        {
            "vendas": vendas,
            "form": form,
        },
    )


@login_required
def detalhes_venda(request, venda_id):
    venda = get_object_or_404(
        vendas_visiveis_para(request.user),
        id=venda_id,
    )

    itens = venda.itens.select_related("product")

    return render(
        request,
        "vendas/detalhes_venda.html",
        {
            "venda": venda,
            "itens": itens,
        },
    )
