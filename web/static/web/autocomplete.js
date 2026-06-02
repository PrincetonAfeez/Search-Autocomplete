(function () {
  const input = document.querySelector("#search-input");
  const suggestions = document.querySelector("#suggestions");

  if (!input || !suggestions) {
    return;
  }

  let activeIndexOnSwap = -1;
  let suppressSwap = false;

  window.__autocompleteSuppressSwap = false;

  function options() {
    return Array.from(suggestions.querySelectorAll(".suggestion-option"));
  }

  function clearActive(items) {
    items.forEach((item) => {
      item.classList.remove("is-active");
      item.setAttribute("aria-selected", "false");
    });
    input.removeAttribute("aria-activedescendant");
  }

  function activeIndex(items) {
    return items.findIndex((item) => item.classList.contains("is-active"));
  }

  function activate(items, index) {
    clearActive(items);

    const item = items[index];
    if (item) {
      item.classList.add("is-active");
      item.setAttribute("aria-selected", "true");
      if (item.id) {
        input.setAttribute("aria-activedescendant", item.id);
      }
      item.scrollIntoView({ block: "nearest" });
    }
  }

  function closeListbox() {
    suppressSwap = true;
    window.__autocompleteSuppressSwap = true;
    suggestions.innerHTML = "";
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
    input.removeAttribute("aria-controls");
    activeIndexOnSwap = -1;
  }

  function select(item) {
    if (!item) {
      return;
    }

    input.value = item.dataset.word || "";
    closeListbox();
    input.focus();
  }

  function syncExpanded() {
    const listbox = suggestions.querySelector(".suggestion-list");
    if (listbox) {
      input.setAttribute("aria-expanded", "true");
      input.setAttribute("aria-controls", listbox.id);

      const items = options();
      if (items.length && activeIndexOnSwap >= 0 && activeIndexOnSwap < items.length) {
        activate(items, activeIndexOnSwap);
      } else if (items.length) {
        clearActive(items);
      }
    } else {
      input.setAttribute("aria-expanded", "false");
      input.removeAttribute("aria-controls");
    }
  }

  const expandedObserver = new MutationObserver(syncExpanded);
  expandedObserver.observe(suggestions, { childList: true, subtree: true });
  syncExpanded();

  document.body.addEventListener("htmx:beforeRequest", (event) => {
    if (event.detail.elt === input) {
      suppressSwap = false;
      window.__autocompleteSuppressSwap = false;
      activeIndexOnSwap = -1;
      input.setAttribute("aria-busy", "true");
    }
  });

  document.body.addEventListener("htmx:afterRequest", (event) => {
    if (event.detail.elt === input) {
      input.setAttribute("aria-busy", "false");
    }
  });

  document.body.addEventListener("htmx:beforeSwap", (event) => {
    if (suppressSwap && event.detail.target === suggestions) {
      event.preventDefault();
    }
  });

  input.addEventListener("keydown", (event) => {
    const items = options();
    if (!items.length) {
      if (event.key === "Escape") {
        closeListbox();
      }
      return;
    }

    const current = activeIndex(items);

    if (event.key === "ArrowDown") {
      event.preventDefault();
      const next = current < items.length - 1 ? current + 1 : 0;
      activeIndexOnSwap = next;
      activate(items, next);
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      const next = current > 0 ? current - 1 : items.length - 1;
      activeIndexOnSwap = next;
      activate(items, next);
    }

    if (event.key === "Enter" && current >= 0) {
      event.preventDefault();
      select(items[current]);
    }

    if (event.key === "Tab") {
      if (current >= 0) {
        event.preventDefault();
        select(items[current]);
      } else {
        closeListbox();
      }
    }

    if (event.key === "Escape") {
      closeListbox();
    }
  });

  suggestions.addEventListener("click", (event) => {
    const option = event.target.closest(".suggestion-option");
    select(option);
  });

  suggestions.addEventListener("pointerenter", (event) => {
    const option = event.target.closest(".suggestion-option");
    if (!option) {
      return;
    }

    const items = options();
    const index = items.indexOf(option);
    if (index >= 0) {
      activeIndexOnSwap = index;
      activate(items, index);
    }
  });

  document.addEventListener("pointerdown", (event) => {
    if (event.target === input || input.contains(event.target)) {
      return;
    }
    if (event.target === suggestions || suggestions.contains(event.target)) {
      return;
    }
    closeListbox();
  });
})();
