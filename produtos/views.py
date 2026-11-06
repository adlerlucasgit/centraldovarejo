from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from .models import Produto


@login_required
@permission_required("produtos.view_produto", raise_exception=True)
def listar_produtos(request):
    produtos = Produto.objects.filter(ativo=True)

    return render(request, "produtos/listar.html", {"produtos": produtos})
