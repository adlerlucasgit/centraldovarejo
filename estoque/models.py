from django.db import models

from produtos.models import Produto


class Estoque(models.Model):
    produto = models.OneToOneField(
        Produto,
        on_delete=models.PROTECT,
        related_name="estoque",
        verbose_name="Produto",
    )

    current_stock = models.PositiveIntegerField(
        default=0,
        verbose_name="Quantidade em estoque",
    )

    class Meta:
        verbose_name = "Estoque"
        verbose_name_plural = "Estoques"

    def __str__(self):
        return f"{self.produto.nome} - {self.current_stock} unidades"


class MovimentacaoEstoque(models.Model):
    class Tipo(models.TextChoices):
        ENTRADA = "ENTRADA", "Entrada"
        AJUSTE = "AJUSTE", "Ajuste"
        VENDA = "VENDA", "Venda"

    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name="movimentacoes_estoque",
        verbose_name="Produto",
    )

    tipo = models.CharField(
        max_length=10,
        choices=Tipo.choices,
        verbose_name="Tipo de movimentação",
    )

    quantity = models.PositiveIntegerField(
        verbose_name="Quantidade",
    )

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        verbose_name="Usuário responsável",
    )

    date_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data e horário",
    )

    reason = models.TextField(
        blank=True,
        verbose_name="Motivo ou observação",
    )

    class Meta:
        ordering = ["-date_time"]
        verbose_name = "Movimentação de estoque"
        verbose_name_plural = "Movimentações de estoque"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="movimentacao_quantidade_maior_que_zero",
            ),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.produto.nome}"
