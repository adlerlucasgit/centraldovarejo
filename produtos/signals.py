from django.contrib.auth.models import Group
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .permissoes import configurar_permissoes_grupo_produtos


@receiver(post_migrate)
def configurar_permissoes_produtos(sender, **kwargs):
    if sender.name != "produtos":
        return

    grupos = Group.objects.filter(name__in=["Administrador", "Caixa"])

    for grupo in grupos:
        configurar_permissoes_grupo_produtos(grupo)
