from decimal import Decimal
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import transaction

from estoque.models import Estoque, MovimentacaoEstoque
from .models import Venda, ItemVenda


@transaction.atomic
def finalizar_venda(*, user, itens, payment_method):
    """
    Finaliza uma venda, registra seus itens,
    atualiza o estoque e registra as movimentações.

    Formato esperado para itens:
    [
        {"produto_id": 1, "quantidade": 2},
        {"produto_id": 2, "quantidade": 1},
    ]
    """

    if not itens:
        raise ValidationError("A venda precisa ter pelo menos um produto.")

    if payment_method not in Venda.FormaPagamento.values:
        raise ValidationError("Forma de pagamento inválida.")

    # Agrupa produtos repetidos no carrinho.
    quantidades = {}

    for item in itens:
        try:
            produto_id = int(item["produto_id"])
            quantidade = int(item["quantidade"])
        except (KeyError, TypeError, ValueError):
            raise ValidationError("Dados de produto ou quantidade inválidos.")

        if quantidade <= 0:
            raise ValidationError("A quantidade deve ser maior que zero.")

        quantidades[produto_id] = quantidades.get(produto_id, 0) + quantidade

    # Confere o estoque de todos os produtos antes de finalizar.
    estoques = {}

    for produto_id, quantidade in quantidades.items():
        try:
            estoque = (
                Estoque.objects.select_for_update()
                .select_related("produto")
                .get(
                    produto_id=produto_id,
                    produto__ativo=True,
                )
            )
        except Estoque.DoesNotExist:
            raise ValidationError(
                f"Produto de código interno {produto_id} " "não encontrado ou inativo."
            )

        if estoque.current_stock < quantidade:
            raise ValidationError(
                f"Estoque insuficiente para o produto "
                f"{estoque.produto.nome}. "
                f"Disponível: {estoque.current_stock}."
            )

        estoques[produto_id] = estoque

    # Cria a venda.
    numero_venda = f"V-{uuid4().hex[:12].upper()}"

    venda = Venda.objects.create(
        number=numero_venda,
        user=user,
        payment_method=payment_method,
        total=Decimal("0.00"),
    )

    total_venda = Decimal("0.00")

    # Registra os itens e atualiza o estoque.
    for produto_id, quantidade in quantidades.items():
        estoque = estoques[produto_id]
        produto = estoque.produto

        preco_unitario = produto.preco
        subtotal = preco_unitario * quantidade

        ItemVenda.objects.create(
            sale=venda,
            product=produto,
            quantity=quantidade,
            unit_price=preco_unitario,
            subtotal=subtotal,
        )

        estoque.current_stock -= quantidade
        estoque.save(update_fields=["current_stock"])

        MovimentacaoEstoque.objects.create(
            produto=produto,
            tipo=MovimentacaoEstoque.Tipo.VENDA,
            quantity=quantidade,
            user=user,
            reason=f"Venda {venda.number}",
        )

        total_venda += subtotal

    # Atualiza o total da venda.
    venda.total = total_venda
    venda.save(update_fields=["total"])

    return venda
