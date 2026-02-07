// JS mínimo (sem dependências). Deixe o comportamento principal no servidor.
// Você pode expandir aqui caso queira filtros/pesquisa no catálogo etc.

(function () {
  document.addEventListener("click", function (event) {
    if (event.target.closest(".cp-stop")) {
      return;
    }
    var card = event.target.closest(".cp-card-clickable");
    if (!card) {
      return;
    }
    var modalId = card.getAttribute("data-modal-id");
    if (!modalId) {
      return;
    }
    var modalEl = document.getElementById(modalId);
    if (!modalEl || !window.bootstrap) {
      return;
    }
    var modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
  });
})();
