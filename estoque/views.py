from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import render, redirect

from .forms import EntradaEstoqueForm, AjusteEstoqueForm
from .models import Estoque, MovimentacaoEstoque


def eh_administrador(user):
    if user.is_authenticated and (
        user.is_superuser or user.groups.filter(name="Administrador").exists()
    ):
        return True

    raise PermissionDenied


def pode_consultar_estoque(user):
    if user.groups.filter(name__in=["Administrador", "Caixa"]).exists():
        return True
    raise PermissionDenied

@login_required
@user_passes_test(eh_administrador)
def registrar_entrada(request):
    if request.method == "POST":
        form = EntradaEstoqueForm(request.POST)

        if form.is_valid():
            produto = form.cleaned_data["produto"]
            quantidade = form.cleaned_data["quantity"]
            observacao = form.cleaned_data["reason"]

            try:
                with transaction.atomic():
                    estoque = Estoque.objects.select_for_update().get(produto=produto)

                    estoque.current_stock += quantidade
                    estoque.save(update_fields=["current_stock"])

                    MovimentacaoEstoque.objects.create(
                        produto=produto,
                        tipo=MovimentacaoEstoque.Tipo.ENTRADA,
                        quantity=quantidade,
                        user=request.user,
                        reason=observacao,
                    )

                messages.success(
                    request,
                    "Entrada de estoque registrada com sucesso.",
                )
                return redirect("registrar_entrada")

            except Estoque.DoesNotExist:
                messages.error(
                    request,
                    "O produto selecionado não possui registro de estoque.",
                )
    else:
        form = EntradaEstoqueForm()

    return render(
        request,
        "estoque/registrar_entrada.html",
        {"form": form},
    )

@login_required
@user_passes_test(eh_administrador)
def registrar_ajuste(request):
    if request.method == "POST":
        form = AjusteEstoqueForm(request.POST)

        if form.is_valid():
            produto = form.cleaned_data["produto"]
            nova_quantidade = form.cleaned_data["current_stock"]
            motivo = form.cleaned_data["reason"]

            try:
                with transaction.atomic():
                    estoque = Estoque.objects.select_for_update().get(produto=produto)

                    saldo_anterior = estoque.current_stock
                    diferenca = abs(nova_quantidade - saldo_anterior)

                    if diferenca == 0:
                        form.add_error(
                            "current_stock",
                            "A nova quantidade deve ser diferente do saldo atual.",
                        )
                    else:
                        estoque.current_stock = nova_quantidade
                        estoque.save(update_fields=["current_stock"])

                        MovimentacaoEstoque.objects.create(
                            produto=produto,
                            tipo=MovimentacaoEstoque.Tipo.AJUSTE,
                            quantity=diferenca,
                            user=request.user,
                            reason=(
                                f"Saldo anterior: {saldo_anterior}. "
                                f"Novo saldo: {nova_quantidade}. "
                                f"Motivo: {motivo}"
                            ),
                        )

                if not form.errors:
                    messages.success(
                        request,
                        "Ajuste de estoque registrado com sucesso.",
                    )
                    return redirect("registrar_ajuste")

            except Estoque.DoesNotExist:
                messages.error(
                    request,
                    "O produto selecionado não possui registro de estoque.",
                )
    else:
        form = AjusteEstoqueForm()

    return render(
        request,
        "estoque/registrar_ajuste.html",
        {"form": form},
    )

@login_required
@user_passes_test(eh_administrador)
def historico_movimentacoes(request):
    movimentacoes = MovimentacaoEstoque.objects.select_related("produto", "user").all()

    return render(
        request,
        "estoque/historico_movimentacoes.html",
        {"movimentacoes": movimentacoes},
    )

@login_required
@user_passes_test(pode_consultar_estoque)
def consultar_estoque(request):
    status = request.GET.get("status", "todos")

    estoques = (
        Estoque.objects.select_related("produto")
        .filter(produto__ativo=True)
        .order_by("produto__nome")
    )

    if status == "baixo":
        estoques = estoques.filter(
            current_stock__gte=1,
            current_stock__lte=20,
        )
    elif status == "sem_estoque":
        estoques = estoques.filter(current_stock=0)
    else:
        status = "todos"

    return render(
        request,
        "estoque/consultar_estoque.html",
        {
            "estoques": estoques,
            "status": status,
        },
    )
