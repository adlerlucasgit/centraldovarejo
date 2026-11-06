from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404

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

@login_required
@permission_required("produtos.change_produto", raise_exception=True)
def editar_produto(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)

    if request.method == "POST":
        form = ProdutoForm(request.POST, instance=produto)

        if form.is_valid():
            form.save()
            return redirect("listar_produtos")
    else:
        form = ProdutoForm(instance=produto)

    return render(
        request,
        "produtos/editar.html",
        {
            "form": form,
            "produto": produto,
        },
    )
