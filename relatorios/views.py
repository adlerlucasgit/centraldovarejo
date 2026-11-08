from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum
from django.shortcuts import render
from django.utils import timezone

from estoque.models import Estoque
from produtos.models import Produto
from vendas.models import Venda, ItemVenda

from .forms import FiltroRelatorioForm


@login_required
def relatorio_geral(request):
    usuario = request.user

    eh_administrador = (
        usuario.is_superuser or usuario.groups.filter(name="Administrador").exists()
    )

    if not eh_administrador:
        raise PermissionDenied

    hoje = timezone.localdate()
    primeiro_dia_mes = hoje.replace(day=1)

    formulario = FiltroRelatorioForm(
        request.GET
        or {
            "data_inicial": primeiro_dia_mes.isoformat(),
            "data_final": hoje.isoformat(),
        }
    )

    if formulario.is_valid():
        data_inicial = formulario.cleaned_data["data_inicial"]
        data_final = formulario.cleaned_data["data_final"]
    else:
        data_inicial = primeiro_dia_mes
        data_final = hoje

    vendas = Venda.objects.filter(
        date_time__date__gte=data_inicial,
        date_time__date__lte=data_final,
    )

    numero_vendas = vendas.count()

    valor_total = vendas.aggregate(total=Sum("total"))["total"] or Decimal("0.00")

    produtos_vendidos = (
        ItemVenda.objects.filter(sale__in=vendas).aggregate(total=Sum("quantity"))[
            "total"
        ]
        or 0
    )

    ticket_medio = valor_total / numero_vendas if numero_vendas else Decimal("0.00")

    produtos_mais_vendidos = (
        ItemVenda.objects.filter(sale__in=vendas)
        .values("product__codigo", "product__nome")
        .annotate(quantidade_vendida=Sum("quantity"))
        .order_by("-quantidade_vendida", "product__nome")[:10]
    )

    pagamentos = (
        vendas.values("payment_method")
        .annotate(quantidade=Count("id"))
        .order_by("-quantidade")
    )

    pagamentos = [
        {
            **pagamento,
            "nome": Venda.FormaPagamento(pagamento["payment_method"]).label,
        }
        for pagamento in pagamentos
    ]

    forma_pagamento_mais_utilizada = None
    ha_empate_pagamento = False

    if pagamentos:
        maior_quantidade = pagamentos[0]["quantidade"]

        formas_mais_utilizadas = [
            pagamento
            for pagamento in pagamentos
            if pagamento["quantidade"] == maior_quantidade
        ]

        if len(formas_mais_utilizadas) == 1:
            forma_pagamento_mais_utilizada = formas_mais_utilizadas[0]
        else:
            ha_empate_pagamento = True

    total_produtos_cadastrados = Produto.objects.count()

    estoque_baixo = Estoque.objects.filter(
        produto__ativo=True,
        current_stock__gte=1,
        current_stock__lte=20,
    ).count()

    estoque_zerado = Estoque.objects.filter(
        produto__ativo=True,
        current_stock=0,
    ).count()

    contexto = {
        "formulario": formulario,
        "data_inicial": data_inicial,
        "data_final": data_final,
        "numero_vendas": numero_vendas,
        "valor_total": valor_total,
        "produtos_vendidos": produtos_vendidos,
        "ticket_medio": ticket_medio,
        "produtos_mais_vendidos": produtos_mais_vendidos,
        "pagamentos": pagamentos,
        "forma_pagamento_mais_utilizada": forma_pagamento_mais_utilizada,
        "ha_empate_pagamento": ha_empate_pagamento,
        "total_produtos_cadastrados": total_produtos_cadastrados,
        "estoque_baixo": estoque_baixo,
        "estoque_zerado": estoque_zerado,
    }

    return render(request, "relatorios/relatorio_geral.html", contexto)
