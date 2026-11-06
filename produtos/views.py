from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect

from .forms import ProdutoForm
from .models import Produto


@login_required
@permission_required("produtos.view_produto", raise_exception=True)
def listar_produtos(request):
    produtos = Produto.objects.filter(ativo=True)

    return render(request, "produtos/listar.html", {"produtos": produtos})


@login_required
@permission_required("produtos.add_produto", raise_exception=True)
def cadastrar_produto(request):
    if request.method == "POST":
        form = ProdutoForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("listar_produtos")
    else:
        form = ProdutoForm()

    return render(request, "produtos/cadastrar.html", {"form": form})
