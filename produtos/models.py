from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Produto(models.Model):
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código")

    nome = models.CharField(max_length=200, verbose_name="Nome")

    preco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Preço de venda",
    )

    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de cadastro")

    atualizado_em = models.DateTimeField(
        auto_now=True, verbose_name="Última atualização"
    )

    class Meta:
        ordering = ["nome"]
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(preco__gt=0), name="produto_preco_maior_que_zero"
            )
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nome}"
