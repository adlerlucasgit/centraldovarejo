from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

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

    form = ItemCarrinhoForm()

    return render(
        request,
        "vendas/iniciar_venda.html",
        {"form": form},
    )
