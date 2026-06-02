// Minimal htmx fallback. Loads alongside htmx.min.js and is a no-op when the
// full library is present (it sets window.htmx); only takes over when htmx
// fails to load (CDN/offline development).
(function () {
  if (window.htmx) {
    return;
  }

  function delayFrom(trigger) {
    const match = trigger.match(/delay:(\d+)ms/);
    return match ? Number(match[1]) : 0;
  }

  function eventsFrom(trigger) {
    const events = new Set();
    if (trigger.includes("keyup")) {
      events.add("keyup");
    }
    if (trigger.includes("changed")) {
      events.add("change");
    }
    if (trigger.includes("search")) {
      events.add("search");
    }
    return events.size ? Array.from(events) : ["change"];
  }

  function withQuery(url, name, value) {
    const separator = url.includes("?") ? "&" : "?";
    return `${url}${separator}${encodeURIComponent(name)}=${encodeURIComponent(value)}`;
  }

  function attach(input) {
    if (input.dataset.htmxLiteAttached === "true") {
      return;
    }

    const url = input.getAttribute("hx-get");
    const target = document.querySelector(input.getAttribute("hx-target"));
    const indicator = document.querySelector(input.getAttribute("hx-indicator"));
    const trigger = input.getAttribute("hx-trigger") || "change";
    const delay = delayFrom(trigger);
    let timeoutId = null;
    let controller = null;

    if (!url || !target) {
      return;
    }

    input.dataset.htmxLiteAttached = "true";

    function request() {
      if (controller) {
        controller.abort();
      }

      controller = typeof AbortController === "undefined" ? null : new AbortController();
      indicator?.classList.add("htmx-request");

      const signal = controller?.signal;
      const requestUrl = withQuery(url, input.name || "q", input.value);

      const xhr = new XMLHttpRequest();
      xhr.open("GET", requestUrl, true);
      xhr.setRequestHeader("HX-Request", "true");

      signal?.addEventListener("abort", () => xhr.abort(), { once: true });

      xhr.onload = () => {
        if (window.__autocompleteSuppressSwap) {
          indicator?.classList.remove("htmx-request");
          return;
        }
        if (xhr.status >= 200 && xhr.status < 300) {
          target.innerHTML = xhr.responseText;
        } else {
          target.innerHTML = '<div class="empty-state">Unable to load suggestions</div>';
        }
        indicator?.classList.remove("htmx-request");
      };

      xhr.onerror = () => {
        target.innerHTML = '<div class="empty-state">Unable to load suggestions</div>';
        indicator?.classList.remove("htmx-request");
      };

      xhr.onabort = () => {
        indicator?.classList.remove("htmx-request");
      };

      xhr.send();
    }

    function schedule() {
      window.clearTimeout(timeoutId);
      window.__autocompleteSuppressSwap = false;
      timeoutId = window.setTimeout(request, delay);
    }

    for (const eventName of eventsFrom(trigger)) {
      input.addEventListener(eventName, schedule);
    }
  }

  function attachAll() {
    const inputs = document.querySelectorAll("[hx-get][hx-target]");
    inputs.forEach(attach);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", attachAll);
  } else {
    attachAll();
  }
})();
