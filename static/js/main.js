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

(function () {
  var editors = document.querySelectorAll("[data-link-editor]");
  if (!editors.length) {
    return;
  }

  function buildEmptyState() {
    var empty = document.createElement("div");
    empty.className = "cp-link-empty text-muted small";
    empty.textContent = "Nenhum link adicionado ainda.";
    return empty;
  }

  editors.forEach(function (editor) {
    var input = editor.querySelector("[data-link-input]");
    var addBtn = editor.querySelector("[data-link-add]");
    var cancelBtn = editor.querySelector("[data-link-cancel]");
    var list = editor.querySelector("[data-link-list]");
    var form = editor.closest("form");
    if (!input || !addBtn || !list || !form) {
      return;
    }
    var textarea = form.querySelector("#id_purchase_links");
    if (!textarea) {
      return;
    }

    var items = [];
    var editingIndex = null;

    function normalize(value) {
      return (value || "").trim();
    }

    function syncTextarea() {
      textarea.value = items.join("\n");
    }

    function setEditing(index) {
      editingIndex = index;
      if (editingIndex === null) {
        addBtn.innerHTML = '<i class="fa-solid fa-plus me-1"></i>Adicionar';
        if (cancelBtn) {
          cancelBtn.classList.add("d-none");
        }
        return;
      }
      addBtn.innerHTML = '<i class="fa-solid fa-check me-1"></i>Salvar';
      if (cancelBtn) {
        cancelBtn.classList.remove("d-none");
      }
    }

    function render() {
      list.innerHTML = "";
      if (!items.length) {
        list.appendChild(buildEmptyState());
        return;
      }
      items.forEach(function (item, index) {
        var row = document.createElement("div");
        row.className = "cp-link-item";

        var text = document.createElement("div");
        text.className = "cp-link-text";
        text.textContent = item;

        var actions = document.createElement("div");
        actions.className = "cp-link-actions";

        var editBtn = document.createElement("button");
        editBtn.type = "button";
        editBtn.className = "btn btn-sm btn-outline-secondary";
        editBtn.innerHTML = '<i class="fa-solid fa-pen-to-square"></i>';
        editBtn.setAttribute("aria-label", "Editar link");
        editBtn.addEventListener("click", function () {
          input.value = item;
          input.focus();
          setEditing(index);
        });

        var deleteBtn = document.createElement("button");
        deleteBtn.type = "button";
        deleteBtn.className = "btn btn-sm btn-outline-danger";
        deleteBtn.innerHTML = '<i class="fa-solid fa-trash"></i>';
        deleteBtn.setAttribute("aria-label", "Excluir link");
        deleteBtn.addEventListener("click", function () {
          items.splice(index, 1);
          if (editingIndex === index) {
            input.value = "";
            setEditing(null);
          } else if (editingIndex !== null && index < editingIndex) {
            editingIndex -= 1;
          }
          syncTextarea();
          render();
        });

        actions.appendChild(editBtn);
        actions.appendChild(deleteBtn);
        row.appendChild(text);
        row.appendChild(actions);
        list.appendChild(row);
      });
    }

    function addCurrent() {
      var value = normalize(input.value);
      if (!value) {
        return;
      }
      if (editingIndex !== null) {
        items[editingIndex] = value;
        setEditing(null);
      } else if (!items.includes(value)) {
        items.push(value);
      }
      input.value = "";
      syncTextarea();
      render();
    }

    function loadFromTextarea() {
      var raw = textarea.value || "";
      items = raw
        .split(/\r?\n/)
        .map(function (line) {
          return normalize(line);
        })
        .filter(Boolean);
    }

    addBtn.addEventListener("click", addCurrent);
    input.addEventListener("keydown", function (event) {
      if (event.key === "Enter") {
        event.preventDefault();
        addCurrent();
      }
    });
    if (cancelBtn) {
      cancelBtn.addEventListener("click", function () {
        input.value = "";
        setEditing(null);
      });
    }

    loadFromTextarea();
    setEditing(null);
    render();
  });
})();

(function () {
  var modalEl = document.getElementById("confirmModal");
  var messageEl = document.getElementById("confirmModalMessage");
  var confirmBtn = document.getElementById("confirmModalConfirm");
  if (!modalEl || !messageEl || !confirmBtn || !window.bootstrap) {
    return;
  }

  var modal = bootstrap.Modal.getOrCreateInstance(modalEl);
  var pendingForm = null;

  document.addEventListener("submit", function (event) {
    var form = event.target.closest("form[data-confirm]");
    if (!form) {
      return;
    }
    if (form.dataset.confirming === "1") {
      form.removeAttribute("data-confirming");
      return;
    }
    event.preventDefault();
    pendingForm = form;
    messageEl.textContent = form.getAttribute("data-confirm") || "Tem certeza?";
    modal.show();
  });

  confirmBtn.addEventListener("click", function () {
    if (!pendingForm) {
      return;
    }
    pendingForm.dataset.confirming = "1";
    modal.hide();
    pendingForm.submit();
    pendingForm = null;
  });
})();
