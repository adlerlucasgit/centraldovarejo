from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from .forms import EntradaEstoqueForm
from .models import Estoque, MovimentacaoEstoque

from django.core.exceptions import PermissionDenied

def eh_administrador(user):
    if not user.groups.filter(name="Administrador").exists():
        raise PermissionDenied

    return True

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
