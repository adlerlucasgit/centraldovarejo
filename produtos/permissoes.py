from django.contrib.auth.models import Permission


def configurar_permissoes_grupo_produtos(grupo):
    permissoes = Permission.objects.filter(
        content_type__app_label="produtos",
        codename__in=[
            "view_produto",
            "add_produto",
            "change_produto",
        ],
    )

    permissoes_por_codigo = {permissao.codename: permissao for permissao in permissoes}

    if grupo.name == "Administrador":
        codigos = [
            "view_produto",
            "add_produto",
            "change_produto",
        ]

        grupo.permissions.add(
            *[
                permissoes_por_codigo[codigo]
                for codigo in codigos
                if codigo in permissoes_por_codigo
            ]
        )

    elif grupo.name == "Caixa":
        grupo.permissions.remove(
            *[
                permissao
                for codigo, permissao in permissoes_por_codigo.items()
                if codigo in ["add_produto", "change_produto"]
            ]
        )

        if "view_produto" in permissoes_por_codigo:
            grupo.permissions.add(permissoes_por_codigo["view_produto"])
