from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from functools import wraps
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.db.models.deletion import ProtectedError

from .forms import UsuarioCriacaoForm, UsuarioEdicaoForm

User = get_user_model()


def eh_administrador(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name="Administrador").exists()
    )


def administrador_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not eh_administrador(request.user):
            raise PermissionDenied

        return view_func(request, *args, **kwargs)

    return login_required(_wrapped_view)


@administrador_required
def listar_usuarios(request):
    usuarios = User.objects.prefetch_related("groups").all().order_by("username")

    busca = request.GET.get("busca", "").strip()
    status = request.GET.get("status", "todos")

    if busca:
        usuarios = usuarios.filter(
            Q(username__icontains=busca)
            | Q(first_name__icontains=busca)
            | Q(last_name__icontains=busca)
            | Q(email__icontains=busca)
        )

    if status == "ativos":
        usuarios = usuarios.filter(is_active=True)
    elif status == "inativos":
        usuarios = usuarios.filter(is_active=False)
    else:
        status = "todos"

    return render(
        request,
        "usuarios/listar.html",
        {
            "usuarios": usuarios,
            "busca": busca,
            "status": status,
        },
    )


@administrador_required
def cadastrar_usuario(request):
    if request.method == "POST":
        form = UsuarioCriacaoForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Usuário cadastrado com sucesso.",
            )

            return redirect("listar_usuarios")
    else:
        form = UsuarioCriacaoForm()

    return render(
        request,
        "usuarios/cadastrar.html",
        {"form": form},
    )


@administrador_required
def editar_usuario(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)

    if request.method == "POST":
        form = UsuarioEdicaoForm(request.POST, instance=usuario)

        if form.is_valid():
            perfil = form.cleaned_data["perfil"]
            ativo = form.cleaned_data["is_active"]

            if usuario.is_superuser and (perfil != "Administrador" or not ativo):
                messages.error(
                    request,
                    "Não é permitido remover o perfil administrativo ou suspender uma conta de superusuário.",
                )
            elif usuario.id == request.user.id and (
                perfil != "Administrador" or not ativo
            ):
                messages.error(
                    request,
                    "Você não pode remover seu próprio perfil administrativo ou suspender sua conta.",
                )
            else:
                form.save()
                messages.success(request, "Usuário atualizado com sucesso.")
                return redirect("listar_usuarios")
    else:
        form = UsuarioEdicaoForm(instance=usuario)

    return render(
        request,
        "usuarios/editar.html",
        {"form": form, "usuario": usuario},
    )


@administrador_required
@require_POST
def suspender_usuario(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)

    if usuario.id == request.user.id:
        messages.error(
            request,
            "Você não pode suspender sua própria conta.",
        )
        return redirect("listar_usuarios")

    if usuario.is_superuser:
        messages.error(
            request,
            "Não é permitido suspender uma conta de superusuário por esta tela.",
        )
        return redirect("listar_usuarios")

    usuario.is_active = False
    usuario.save(update_fields=["is_active"])

    messages.success(
        request,
        "Usuário suspenso com sucesso.",
    )

    return redirect("listar_usuarios")


@administrador_required
@require_POST
def reativar_usuario(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)

    if usuario.is_superuser:
        messages.error(
            request,
            "Esta conta de superusuário não precisa ser reativada por esta tela.",
        )
        return redirect("listar_usuarios")

    usuario.is_active = True
    usuario.save(update_fields=["is_active"])

    messages.success(
        request,
        "Usuário reativado com sucesso.",
    )

    return redirect("listar_usuarios")


@administrador_required
@require_POST
def excluir_usuario(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)

    if usuario.id == request.user.id:
        messages.error(
            request,
            "Você não pode excluir sua própria conta.",
        )
        return redirect("listar_usuarios")

    if usuario.is_superuser:
        messages.error(
            request,
            "Não é permitido excluir uma conta de superusuário por esta tela.",
        )
        return redirect("listar_usuarios")

    try:
        usuario.delete()
    except ProtectedError:
        messages.error(
            request,
            "Este usuário não pode ser excluído porque possui vendas registradas.",
        )
        return redirect("listar_usuarios")

    messages.success(
        request,
        "Usuário excluído com sucesso.",
    )

    return redirect("listar_usuarios")
