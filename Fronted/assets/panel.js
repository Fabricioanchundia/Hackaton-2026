(function () {
  "use strict";

  var BASE_REFRESH_MS = 30000;
  var MAX_REFRESH_MS = 120000;
  var REQUEST_TIMEOUT_MS = 12000;

  var elements = {
    connectionBadge: document.getElementById("connectionBadge"),
    caseCount: document.getElementById("caseCount"),
    lastUpdated: document.getElementById("lastUpdated"),
    refreshButton: document.getElementById("refreshButton"),
    panelStatus: document.getElementById("panelStatus"),
    casesBody: document.getElementById("casesBody"),
    emptyState: document.getElementById("emptyState"),
    tableWrap: document.querySelector(".table-wrap")
  };

  var state = {
    loading: false,
    timer: null,
    refreshDelay: BASE_REFRESH_MS,
    hasLoaded: false
  };

  function ApiError(message, code) {
    this.name = "ApiError";
    this.message = message;
    this.code = code || "request_failed";
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ApiError);
    }
  }

  ApiError.prototype = Object.create(Error.prototype);
  ApiError.prototype.constructor = ApiError;

  async function requestJSON(path, timeoutMs) {
    var controller = new AbortController();
    var timeout = window.setTimeout(function () { controller.abort(); }, timeoutMs || REQUEST_TIMEOUT_MS);
    try {
      var response = await fetch(path, {
        headers: { "Accept": "application/json" },
        signal: controller.signal
      });
      var raw = await response.text();
      var data = {};
      if (raw) {
        try {
          data = JSON.parse(raw);
        } catch (parseError) {
          throw new ApiError("El servidor respondió en un formato inesperado.", "invalid_response");
        }
      }
      if (!response.ok) {
        throw new ApiError(data.detalle || data.error || "No se pudo actualizar el panel.", "http_" + response.status);
      }
      return data;
    } catch (error) {
      if (error.name === "AbortError") {
        throw new ApiError("La actualización está tardando más de lo esperado.", "timeout");
      }
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError("No pudimos conectar con ManabIA.", "network");
    } finally {
      window.clearTimeout(timeout);
    }
  }

  function setConnection(mode, text) {
    elements.connectionBadge.classList.remove("is-online", "is-simulated", "is-offline");
    elements.connectionBadge.classList.add(mode === "real" ? "is-online" : mode === "simulado" ? "is-simulated" : "is-offline");
    elements.connectionBadge.lastElementChild.textContent = text;
  }

  function setStatus(text, tone) {
    elements.panelStatus.textContent = text || "";
    elements.panelStatus.className = "status" + (tone ? " is-" + tone : "");
  }

  function safeText(value, fallback) {
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
    return fallback || "—";
  }

  function formatDate(value) {
    if (!value) {
      return "Sin fecha";
    }
    var date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return safeText(value, "Sin fecha");
    }
    return new Intl.DateTimeFormat("es-EC", {
      dateStyle: "medium",
      timeStyle: "short"
    }).format(date);
  }

  function appendCell(row, label, className) {
    var cell = document.createElement("td");
    cell.dataset.label = label;
    if (className) {
      cell.className = className;
    }
    row.appendChild(cell);
    return cell;
  }

  function renderCases(cases) {
    var orderedCases = cases.slice().sort(function (left, right) {
      return Number(right.intentos || 0) - Number(left.intentos || 0);
    });
    elements.casesBody.replaceChildren();
    elements.caseCount.textContent = String(cases.length);
    elements.emptyState.hidden = cases.length !== 0;
    elements.tableWrap.hidden = cases.length === 0;

    orderedCases.forEach(function (item) {
      var row = document.createElement("tr");

      var studentCell = appendCell(row, "Estudiante", "student-cell");
      var studentName = document.createElement("strong");
      studentName.textContent = safeText(item.estudiante, "Estudiante anónimo");
      var signal = document.createElement("span");
      signal.textContent = "Semáforo rojo · revisión humana";
      studentCell.appendChild(studentName);
      studentCell.appendChild(signal);

      var topicCell = appendCell(row, "Tema");
      topicCell.textContent = safeText(item.tema, "Tema sin especificar");

      var evidenceCell = appendCell(row, "Motivo y evidencia", "evidence-cell");
      var reason = document.createElement("strong");
      reason.textContent = safeText(item.motivo, "Tres respuestas consecutivas en rojo.");
      evidenceCell.appendChild(reason);
      if (item.respuesta) {
        var answer = document.createElement("span");
        answer.textContent = "Última respuesta: “" + safeText(item.respuesta, "Sin respuesta") + "”";
        evidenceCell.appendChild(answer);
      }

      var attemptsCell = appendCell(row, "Intentos");
      var attempts = document.createElement("span");
      attempts.className = "attempt-badge";
      attempts.textContent = String(Number.isFinite(Number(item.intentos)) ? Number(item.intentos) : 3) + " intentos";
      attemptsCell.appendChild(attempts);

      var dateCell = appendCell(row, "Fecha", "date-cell");
      dateCell.textContent = formatDate(item.fecha);

      elements.casesBody.appendChild(row);
    });
  }

  function scheduleRefresh() {
    window.clearTimeout(state.timer);
    if (document.hidden) {
      return;
    }
    state.timer = window.setTimeout(function () {
      loadCases(true);
    }, state.refreshDelay);
  }

  async function loadCases(silent) {
    if (state.loading) {
      return;
    }
    state.loading = true;
    elements.refreshButton.disabled = true;
    if (!silent || !state.hasLoaded) {
      setStatus("Actualizando casos…");
    }

    try {
      var data = await requestJSON("/api/escalados");
      if (!data || !Array.isArray(data.escalados)) {
        throw new ApiError("La lista de casos llegó incompleta.", "invalid_response");
      }
      renderCases(data.escalados);
      state.hasLoaded = true;
      state.refreshDelay = BASE_REFRESH_MS;
      elements.lastUpdated.textContent = "Actualizado " + new Intl.DateTimeFormat("es-EC", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
      }).format(new Date());
      if (!silent) {
        setStatus(
          data.escalados.length ? "Revisa primero los casos con más intentos." : "El panel está al día.",
          "success"
        );
      }
      if (data.modo === "real") {
        setConnection("real", "IA conectada");
      } else if (data.modo === "simulado") {
        setConnection("simulado", "Demo sin consumo de API");
      }
    } catch (error) {
      state.refreshDelay = Math.min(state.refreshDelay * 2, MAX_REFRESH_MS);
      setConnection("offline", error.code === "timeout" ? "Actualización demorada" : "Conexión intermitente");
      setStatus(error.message + " Conservamos los últimos datos visibles; usa Actualizar para reintentar.", "error");
      if (!state.hasLoaded) {
        elements.caseCount.textContent = "—";
      }
    } finally {
      state.loading = false;
      elements.refreshButton.disabled = false;
      scheduleRefresh();
    }
  }

  async function checkMode() {
    if (!navigator.onLine) {
      setConnection("offline", "Navegador sin red");
      return;
    }
    try {
      var data = await requestJSON("/api/estado", 5000);
      if (data.modo === "real") {
        setConnection("real", "IA conectada");
      } else {
        setConnection("simulado", "Demo sin consumo de API");
      }
    } catch (error) {
      setConnection("offline", "Panel no disponible");
    }
  }

  elements.refreshButton.addEventListener("click", function () {
    loadCases(false);
  });

  document.addEventListener("visibilitychange", function () {
    if (document.hidden) {
      window.clearTimeout(state.timer);
    } else {
      loadCases(true);
    }
  });

  window.addEventListener("offline", function () {
    setConnection("offline", "Navegador sin red");
  });

  window.addEventListener("online", function () {
    checkMode();
    loadCases(true);
  });

  checkMode();
  loadCases(false);
})();
