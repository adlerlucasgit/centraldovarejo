from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from decimal import Decimal

from produtos.models import Produto


class Venda(models.Model):

    class FormaPagamento(models.TextChoices):
        DINHEIRO = "DINHEIRO", "Dinheiro"
        CARTAO = "CARTAO", "Cartão"
        PIX = "PIX", "PIX"

    number = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Número da venda",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="vendas",
        verbose_name="Operador",
    )

    date_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data e horário",
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Total da venda",
    )

    payment_method = models.CharField(
        max_length=10,
        choices=FormaPagamento.choices,
        verbose_name="Forma de pagamento",
    )

    class Meta:
        ordering = ["-date_time"]
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"

    def __str__(self):
        return f"Venda {self.number}"


class ItemVenda(models.Model):

    sale = models.ForeignKey(
        Venda,
        on_delete=models.PROTECT,
        related_name="itens",
        verbose_name="Venda",
    )

    product = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name="itens_venda",
        verbose_name="Produto",
    )

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Quantidade",
    )

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Preço unitário",
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Subtotal",
    )

    class Meta:
        verbose_name = "Item da venda"
        verbose_name_plural = "Itens da venda"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="item_venda_quantidade_maior_que_zero",
            ),
        ]

    def __str__(self):
        return f"{self.product.nome} - {self.quantity} unidades"
