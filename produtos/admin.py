from django.contrib import admin

from .models import Produto


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nome",
        "preco",
        "ativo",
        "criado_em",
    )

    list_filter = ("ativo", "criado_em")

    search_fields = ("codigo", "nome")

    ordering = ("nome",)

    readonly_fields = ("criado_em", "atualizado_em")

    list_per_page = 20

    def has_delete_permission(self, request, obj=None):
        return False
