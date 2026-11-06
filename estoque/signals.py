from django.db.models.signals import post_save
from django.dispatch import receiver

from produtos.models import Produto

from .models import Estoque


@receiver(post_save, sender=Produto)
def criar_estoque_automaticamente(sender, instance, created, **kwargs):
    if created:
        Estoque.objects.get_or_create(
            produto=instance,
            defaults={"current_stock": 0},
        )
