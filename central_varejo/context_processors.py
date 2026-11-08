def perfil_usuario(request):
    usuario = request.user

    if not usuario.is_authenticated:
        return {
            "eh_administrador": False,
            "eh_caixa": False,
            "pode_operar_vendas": False,
            "pode_consultar_estoque": False,
            "pode_gerenciar_estoque": False,
            "pode_ver_relatorios": False,
        }

    pertence_administrador = usuario.groups.filter(name="Administrador").exists()

    pertence_caixa = usuario.groups.filter(name="Caixa").exists()

    eh_administrador = usuario.is_superuser or pertence_administrador
    eh_caixa = pertence_caixa and not eh_administrador

    return {
        "eh_administrador": eh_administrador,
        "eh_caixa": eh_caixa,
        "pode_operar_vendas": eh_administrador or eh_caixa,
        "pode_consultar_estoque": eh_administrador or eh_caixa,
        "pode_gerenciar_estoque": eh_administrador,
        "pode_ver_relatorios": eh_administrador,
    }
