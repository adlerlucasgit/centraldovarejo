
document.addEventListener("DOMContentLoaded", () => {
    const modalElement = document.getElementById("modalConfirmacao");

    if (!modalElement || typeof bootstrap === "undefined") {
        return;
    }

    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);

    const titulo = document.getElementById("confirmacaoTitulo");
    const mensagem = document.getElementById("confirmacaoMensagem");
    const icone = document.getElementById("confirmacaoIcone");
    const botaoConfirmar = document.getElementById("confirmacaoBotao");

    let formularioPendente = null;
    let botaoOrigem = null;

    const estilos = {
        danger: {
            botao: "btn-danger",
            icone: "bi-exclamation-triangle-fill",
            cor: "text-danger"
        },
        warning: {
            botao: "btn-warning",
            icone: "bi-exclamation-circle-fill",
            cor: "text-warning"
        },
        success: {
            botao: "btn-success",
            icone: "bi-check-circle-fill",
            cor: "text-success"
        },
        primary: {
            botao: "btn-primary",
            icone: "bi-info-circle-fill",
            cor: "text-primary"
        }
    };

    // Intercepta somente formulários que solicitam confirmação.
    document.addEventListener("submit", (event) => {
        const formulario = event.target;

        if (!(formulario instanceof HTMLFormElement)) {
            return;
        }

        // Permite o envio após a confirmação.
        if (formulario.dataset.confirmado === "true") {
            delete formulario.dataset.confirmado;
            return;
        }

        if (!formulario.hasAttribute("data-confirm")) {
            return;
        }

        event.preventDefault();

        formularioPendente = formulario;
        botaoOrigem = event.submitter;

        const estilo = estilos[formulario.dataset.confirmTipo] || estilos.primary;

        titulo.textContent =
            formulario.dataset.confirmTitulo || "Confirmar ação";

        mensagem.textContent =
            formulario.dataset.confirm || "Deseja realmente continuar?";

        icone.className = `bi ${estilo.icone} ${estilo.cor} fs-1`;

        botaoConfirmar.className = `btn ${estilo.botao}`;
        botaoConfirmar.textContent =
            formulario.dataset.confirmBotao || "Confirmar";

        modal.show();
    });

    // Executa a ação somente após a confirmação.
    botaoConfirmar.addEventListener("click", () => {
        if (!formularioPendente) {
            return;
        }

        const formulario = formularioPendente;
        const botao = botaoOrigem;

        formularioPendente = null;
        botaoOrigem = null;

        if (!formulario.isConnected) {
            return;
        }

        formulario.dataset.confirmado = "true";

        modal.hide();

        if (botao && botao.form === formulario) {
            formulario.requestSubmit(botao);
        } else {
            formulario.requestSubmit();
        }
    });

    // Descarta a ação quando o usuário fecha ou cancela o modal.
    modalElement.addEventListener("hidden.bs.modal", () => {
        formularioPendente = null;
        botaoOrigem = null;
    });
});
