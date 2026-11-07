from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_date

from produtos.models import Produto
from estoque.models import Estoque
from vendas.models import Venda


@login_required
def inicio(request):
    usuario = request.user

    eh_administrador = (
        usuario.is_superuser or usuario.groups.filter(name="Administrador").exists()
    )

    eh_caixa = usuario.groups.filter(name="Caixa").exists()

    if not eh_administrador and not eh_caixa:
        raise PermissionDenied

    # Data selecionada no filtro do Dashboard
    data_selecionada = parse_date(request.GET.get("data", ""))

    if data_selecionada is None:
        data_selecionada = timezone.localdate()

    # Produtos cadastrados e ativos
    total_produtos = Produto.objects.filter(ativo=True).count()

    # Quantidade total de unidades disponíveis em estoque
    itens_em_estoque = (
        Estoque.objects.filter(produto__ativo=True).aggregate(
            total=Sum("current_stock")
        )["total"]
        or 0
    )

    # Produtos que precisam de atenção no estoque
    alertas_estoque_baixo = Estoque.objects.filter(
        produto__ativo=True,
        current_stock__lte=20,
    ).count()

    # Vendas permitidas conforme o perfil
    vendas = Venda.objects.select_related("user")

    if not eh_administrador:
        vendas = vendas.filter(user=usuario)

    # Vendas da data selecionada
    vendas_do_dia = vendas.filter(date_time__date=data_selecionada)

    # Valor total das vendas da data selecionada
    total_vendas_dia = vendas_do_dia.aggregate(total=Sum("total"))["total"] or 0

    # Últimas cinco vendas realizadas
    vendas_recentes = vendas.order_by("-date_time")[:5]

    contexto = {
        "eh_administrador": eh_administrador,
        "total_produtos": total_produtos,
        "itens_em_estoque": itens_em_estoque,
        "alertas_estoque_baixo": alertas_estoque_baixo,
        "total_vendas_dia": total_vendas_dia,
        "data_selecionada": data_selecionada,
        "vendas_recentes": vendas_recentes,
    }

    return render(
        request,
        "inicio.html",
        contexto,
    )
