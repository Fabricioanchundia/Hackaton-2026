(function () {
  "use strict";

  var REQUEST_TIMEOUT_MS = 18000;
  var PRACTICE_ROUNDS = 4;

  var elements = {
    connectionBadge: document.getElementById("connectionBadge"),
    topicForm: document.getElementById("topicForm"),
    studentName: document.getElementById("studentName"),
    topicSelect: document.getElementById("topicSelect"),
    customTopicField: document.getElementById("customTopicField"),
    customTopic: document.getElementById("customTopic"),
    sourceText: document.getElementById("sourceText"),
    startButton: document.getElementById("startButton"),
    chat: document.getElementById("chat"),
    status: document.getElementById("status"),
    responseForm: document.getElementById("responseForm"),
    studentAnswer: document.getElementById("studentAnswer"),
    sendButton: document.getElementById("sendButton"),
    stepLearn: document.getElementById("stepLearn"),
    stepCheck: document.getElementById("stepCheck"),
    stepPractice: document.getElementById("stepPractice"),
    practicePanel: document.getElementById("practicePanel"),
    closePracticeButton: document.getElementById("closePracticeButton"),
    teamCards: [document.getElementById("teamCard0"), document.getElementById("teamCard1")],
    scores: [document.getElementById("score0"), document.getElementById("score1")],
    roundLabel: document.getElementById("roundLabel"),
    turnLabel: document.getElementById("turnLabel"),
    practiceLoading: document.getElementById("practiceLoading"),
    practiceQuestionBlock: document.getElementById("practiceQuestionBlock"),
    practiceQuestion: document.getElementById("practiceQuestion"),
    practiceOptions: document.getElementById("practiceOptions"),
    practiceFeedback: document.getElementById("practiceFeedback"),
    nextQuestionButton: document.getElementById("nextQuestionButton"),
    practiceError: document.getElementById("practiceError"),
    retryPracticeButton: document.getElementById("retryPracticeButton"),
    practiceContent: document.getElementById("practiceContent")
  };

  var state = {
    topic: "",
    source: "",
    student: "",
    explanation: "",
    question: "",
    understood: false,
    loadingExplanation: false,
    evaluating: false,
    session: 0,
    pendingEvaluation: null,
    shownWarnings: {},
    practice: null
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

  function createAttemptId() {
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
      return window.crypto.randomUUID();
    }
    return "intento-" + Date.now() + "-" + Math.random().toString(16).slice(2);
  }

  function isConnectivityIssue(error) {
    if (!error || !error.code) {
      return true;
    }
    if (error.code === "network" || error.code === "timeout" || error.code === "invalid_response") {
      return true;
    }
    if (error.code.indexOf("http_") === 0) {
      return Number(error.code.slice(5)) >= 500;
    }
    return false;
  }

  async function requestJSON(path, options) {
    var config = options || {};
    var controller = new AbortController();
    var timeout = window.setTimeout(function () {
      controller.abort();
    }, config.timeout || REQUEST_TIMEOUT_MS);

    var fetchOptions = {
      method: config.method || "GET",
      headers: { "Accept": "application/json" },
      signal: controller.signal
    };

    if (config.body !== undefined) {
      fetchOptions.headers["Content-Type"] = "application/json";
      fetchOptions.body = JSON.stringify(config.body);
    }

    try {
      var response = await fetch(path, fetchOptions);
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
        throw new ApiError(data.detalle || data.error || "No se pudo completar la solicitud.", "http_" + response.status);
      }

      return data;
    } catch (error) {
      if (error.name === "AbortError") {
        throw new ApiError("La respuesta está tardando más de lo esperado.", "timeout");
      }
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError("No pudimos conectar con Kosko. Revisa la conexión.", "network");
    } finally {
      window.clearTimeout(timeout);
    }
  }

  function setConnection(mode, label) {
    var badge = elements.connectionBadge;
    badge.classList.remove("is-online", "is-simulated", "is-offline");
    badge.classList.add(mode === "real" ? "is-online" : mode === "simulado" ? "is-simulated" : "is-offline");
    badge.lastElementChild.textContent = label;
  }

  function reflectMode(data) {
    if (!data || !data.modo) {
      return;
    }
    if (data.modo === "real") {
      setConnection("real", "IA conectada");
    } else {
      setConnection("simulado", "Demo sin consumo de API");
    }

    if (data.aviso && !state.shownWarnings[data.aviso]) {
      state.shownWarnings[data.aviso] = true;
      addMessage({
        author: "Conexión protegida",
        text: data.aviso + " Continuamos con contenido de demostración para no interrumpir tu aprendizaje.",
        tone: "warning"
      });
    }
  }

  function setStatus(text, tone) {
    elements.status.textContent = text || "";
    elements.status.className = "status" + (tone ? " is-" + tone : "");
  }

  function setSteps(activeStep) {
    var steps = [elements.stepLearn, elements.stepCheck, elements.stepPractice];
    var activeIndex = activeStep === "learn" ? 0 : activeStep === "check" ? 1 : 2;
    steps.forEach(function (step, index) {
      step.classList.toggle("is-active", index === activeIndex);
      step.classList.toggle("is-complete", index < activeIndex);
    });
  }

  function createButton(label, className, onClick) {
    var button = document.createElement("button");
    button.type = "button";
    button.className = "button " + (className || "button--secondary");
    button.textContent = label;
    button.addEventListener("click", onClick);
    return button;
  }

  function addMessage(options) {
    var config = options || {};
    var isStudent = config.role === "student";
    var article = document.createElement("article");
    article.className = "message " + (isStudent ? "message--student" : "message--agent");
    if (config.tone) {
      article.classList.add("message--" + config.tone);
    }

    var avatar = document.createElement("span");
    avatar.className = "message__avatar";
    avatar.setAttribute("aria-hidden", "true");
    avatar.textContent = isStudent ? (state.student.charAt(0).toUpperCase() || "E") : "K";

    var bubble = document.createElement("div");
    bubble.className = "message__bubble";

    var author = document.createElement("span");
    author.className = "message__author";
    author.textContent = config.author || (isStudent ? state.student || "Estudiante" : "Kosko");
    bubble.appendChild(author);

    var paragraph = document.createElement("p");
    paragraph.textContent = config.text || "";
    bubble.appendChild(paragraph);

    if (config.semaphore) {
      var meta = document.createElement("div");
      meta.className = "message__meta";
      var semaphore = document.createElement("span");
      semaphore.className = "semaphore semaphore--" + config.semaphore;
      var dot = document.createElement("span");
      dot.className = "semaphore__dot";
      dot.setAttribute("aria-hidden", "true");
      semaphore.appendChild(dot);
      semaphore.appendChild(document.createTextNode("Semáforo " + config.semaphore));
      meta.appendChild(semaphore);
      bubble.appendChild(meta);
    }

    if (config.actions && config.actions.length) {
      var actions = document.createElement("div");
      actions.className = "message__actions";
      config.actions.forEach(function (action) {
        actions.appendChild(createButton(action.label, action.className, action.onClick));
      });
      bubble.appendChild(actions);
    }

    article.appendChild(avatar);
    article.appendChild(bubble);
    elements.chat.appendChild(article);
    elements.chat.scrollTop = elements.chat.scrollHeight;
    return article;
  }

  function addLoadingMessage(label) {
    var article = document.createElement("article");
    article.className = "message message--agent";
    article.setAttribute("aria-label", label);

    var avatar = document.createElement("span");
    avatar.className = "message__avatar";
    avatar.setAttribute("aria-hidden", "true");
    avatar.textContent = "K";

    var bubble = document.createElement("div");
    bubble.className = "message__bubble";
    var author = document.createElement("span");
    author.className = "message__author";
    author.textContent = "Kosko está pensando";
    var dots = document.createElement("div");
    dots.className = "typing-dots";
    dots.setAttribute("aria-hidden", "true");
    dots.appendChild(document.createElement("span"));
    dots.appendChild(document.createElement("span"));
    dots.appendChild(document.createElement("span"));

    bubble.appendChild(author);
    bubble.appendChild(dots);
    article.appendChild(avatar);
    article.appendChild(bubble);
    elements.chat.appendChild(article);
    elements.chat.scrollTop = elements.chat.scrollHeight;
    return article;
  }

  function getTopic() {
    var categoria = elements.topicSelect.options[elements.topicSelect.selectedIndex].text;
    var temaEscrito = elements.customTopic.value.trim();
    if (!temaEscrito) {
      return "";
    }
    if (elements.topicSelect.value === "otro") {
      return temaEscrito;
    }
    return categoria + ": " + temaEscrito;
  }

  function setTopicControlsBusy(isBusy) {
    elements.studentName.disabled = isBusy;
    elements.topicSelect.disabled = isBusy;
    elements.customTopic.disabled = isBusy;
    elements.sourceText.disabled = isBusy;
    elements.startButton.disabled = isBusy;
    elements.startButton.firstElementChild.textContent = isBusy ? "Preparando explicación…" : "Empezar a aprender";
  }

  function setAnswerEnabled(isEnabled) {
    elements.studentAnswer.disabled = !isEnabled;
    elements.sendButton.disabled = !isEnabled;
    elements.studentAnswer.placeholder = isEnabled
      ? "Escribe tu respuesta con tus palabras…"
      : state.understood
        ? "Comprensión verificada · práctica disponible"
        : "Primero elige un tema…";
  }

  function validExplanation(data) {
    return data && typeof data.explicacion === "string" && data.explicacion.trim() &&
      typeof data.pregunta === "string" && data.pregunta.trim();
  }

  async function startLearning(options) {
    var config = options || {};
    if (state.loadingExplanation || state.evaluating) {
      return;
    }

    var topic = getTopic();
    var student = elements.studentName.value.trim();
    if (!student) {
      elements.studentName.focus();
      setStatus("Escribe un nombre o alias para iniciar.", "error");
      return;
    }
    if (!topic) {
      elements.customTopic.focus();
      setStatus("Escribe el tema que quieres aprender.", "error");
      return;
    }

    state.student = student;
    state.topic = topic;
    state.source = elements.sourceText.value.trim();
    state.explanation = "";
    state.question = "";
    state.understood = false;
    state.pendingEvaluation = null;
    state.practice = null;
    state.session += 1;
    var currentSession = state.session;

    try {
      window.localStorage.setItem("manabia_student", student);
    } catch (storageError) {
      // El alias es una comodidad; la tutoría funciona aunque el almacenamiento esté bloqueado.
    }

    if (config.resetChat !== false) {
      elements.chat.replaceChildren();
      addMessage({ role: "student", text: "Quiero aprender sobre " + topic + "." });
    }
    elements.practicePanel.hidden = true;
    setSteps("learn");
    setStatus("Preparando una explicación breve…");
    setTopicControlsBusy(true);
    setAnswerEnabled(false);
    state.loadingExplanation = true;

    var loadingMessage = addLoadingMessage("Kosko está preparando la explicación");

    try {
      var data = await requestJSON("/api/explicar", {
        method: "POST",
        body: { tema: topic, texto: state.source }
      });

      if (currentSession !== state.session) {
        return;
      }
      if (!validExplanation(data)) {
        throw new ApiError("La explicación llegó incompleta.", "invalid_response");
      }

      loadingMessage.remove();
      state.explanation = data.explicacion.trim();
      state.question = data.pregunta.trim();
      addMessage({ text: state.explanation });
      addMessage({
        author: "Comprueba lo aprendido",
        text: state.question,
        tone: "success"
      });
      reflectMode(data);
      setSteps("check");
      setStatus("Responde con tus palabras. No tiene que ser perfecto.", "success");
      setAnswerEnabled(true);
      elements.studentAnswer.focus();
    } catch (error) {
      loadingMessage.remove();
      if (isConnectivityIssue(error)) {
        setConnection("offline", error.code === "timeout" ? "Respuesta lenta" : "Sin conexión con el tutor");
      }
      setStatus("La explicación no se pudo cargar.", "error");
      addMessage({
        author: "No perdimos tu tema",
        text: error.message + " Puedes volver a intentar sin escribirlo de nuevo.",
        tone: "error",
        actions: [{
          label: "Reintentar explicación",
          className: "button--secondary",
          onClick: function () { startLearning({ resetChat: false }); }
        }]
      });
    } finally {
      state.loadingExplanation = false;
      setTopicControlsBusy(false);
    }
  }

  function validEvaluation(data) {
    return data && ["rojo", "amarillo", "verde"].indexOf(data.semaforo) !== -1 &&
      typeof data.razon === "string" && data.razon.trim();
  }

  async function evaluateAnswer(evaluation, isRetry) {
    if (state.evaluating || !state.question) {
      return;
    }

    var pending = evaluation;
    if (!pending) {
      var answer = elements.studentAnswer.value.trim();
      if (!answer) {
        elements.studentAnswer.focus();
        return;
      }
      pending = {
        id: createAttemptId(),
        answer: answer,
        topic: state.topic,
        question: state.question,
        student: state.student,
        session: state.session
      };
      state.pendingEvaluation = pending;
      addMessage({ role: "student", text: answer });
      elements.studentAnswer.value = "";
    }

    if (pending.session !== undefined && pending.session !== state.session) {
      setStatus("Ese reintento pertenece a una tutoría anterior. Responde la pregunta actual.", "error");
      return;
    }

    state.evaluating = true;
    setAnswerEnabled(false);
    setStatus(isRetry ? "Reintentando la misma evaluación…" : "Revisando tu comprensión…");
    var loadingMessage = addLoadingMessage("Kosko está evaluando la respuesta");

    try {
      var data = await requestJSON("/api/evaluar", {
        method: "POST",
        body: {
          tema: pending.topic || state.topic,
          pregunta: pending.question || state.question,
          respuesta: pending.answer,
          estudiante: pending.student || state.student,
          intento_id: pending.id
        }
      });

      if (!validEvaluation(data)) {
        throw new ApiError("La evaluación llegó incompleta.", "invalid_response");
      }

      loadingMessage.remove();
      reflectMode(data);
      var tone = data.semaforo === "verde" ? "success" : data.semaforo === "amarillo" ? "warning" : "danger";
      var actions = [];

      if (data.semaforo === "verde") {
        state.understood = true;
        setSteps("practice");
        elements.studentAnswer.placeholder = "Comprensión verificada · práctica disponible";
        actions.push({
          label: "Practicar lo aprendido (grupal)",
          className: "button--practice",
          onClick: openPractice
        });
        setStatus("Comprensión verificada. Puedes iniciar el refuerzo grupal.", "success");
      } else {
        actions.push({
          label: "Intentar otra respuesta",
          className: "button--secondary",
          onClick: function () {
            setAnswerEnabled(true);
            elements.studentAnswer.focus();
          }
        });
        actions.push({
          label: "Explicarlo otra vez",
          className: "button--secondary",
          onClick: function () { startLearning({ resetChat: false }); }
        });
        setStatus(data.semaforo === "amarillo" ? "Vas por buen camino; prueba una vez más." : "Puedes intentarlo de nuevo o pedir otra explicación.");
      }

      addMessage({
        author: "Evaluación explicada",
        text: data.razon.trim(),
        tone: tone,
        semaphore: data.semaforo,
        actions: actions
      });

      if (data.escalado) {
        addMessage({
          author: "Supervisión docente activada",
          text: "Registramos que este tema necesita apoyo adicional. Tu docente podrá revisar el motivo y acompañarte; la IA no toma esa decisión final.",
          tone: "warning"
        });
      }

      state.pendingEvaluation = null;
      if (data.semaforo !== "verde") {
        setAnswerEnabled(true);
        elements.studentAnswer.focus();
      }
    } catch (error) {
      loadingMessage.remove();
      if (isConnectivityIssue(error)) {
        setConnection("offline", error.code === "timeout" ? "Evaluación demorada" : "Conexión intermitente");
      }
      setStatus("Tu respuesta sigue visible y puede reenviarse con seguridad.", "error");
      addMessage({
        author: "No pudimos confirmar la evaluación",
        text: error.message + " El reintento conserva el mismo identificador para evitar contar tu respuesta dos veces.",
        tone: "error",
        actions: [{
          label: "Reintentar evaluación",
          className: "button--secondary",
          onClick: function () { evaluateAnswer(pending, true); }
        }]
      });
    } finally {
      state.evaluating = false;
    }
  }

  function validPracticeQuestion(data) {
    return data && typeof data.pregunta === "string" && data.pregunta.trim() &&
      Array.isArray(data.opciones) && data.opciones.length === 4 &&
      data.opciones.every(function (option) { return typeof option === "string" && option.trim(); }) &&
      Number.isInteger(data.respuesta_correcta) && data.respuesta_correcta >= 0 && data.respuesta_correcta < 4 &&
      typeof data.explicacion === "string";
  }

  function updateScoreboard() {
    var practice = state.practice;
    elements.scores[0].textContent = String(practice.scores[0]);
    elements.scores[1].textContent = String(practice.scores[1]);
    elements.roundLabel.textContent = "Ronda " + practice.round + " de " + practice.total;
    elements.turnLabel.textContent = "Turno del " + (practice.team === 0 ? "Equipo Ceibo" : "Equipo Colibrí");
    elements.teamCards[0].classList.toggle("is-current", practice.team === 0);
    elements.teamCards[1].classList.toggle("is-current", practice.team === 1);
  }

  function restorePracticeContent() {
    if (elements.turnLabel.parentElement === elements.practiceContent) {
      return;
    }
    elements.practiceContent.replaceChildren();
    elements.practiceContent.appendChild(elements.turnLabel);
    elements.practiceContent.appendChild(elements.practiceLoading);
    elements.practiceContent.appendChild(elements.practiceQuestionBlock);
    elements.practiceContent.appendChild(elements.practiceError);
  }

  function openPractice() {
    if (!state.understood) {
      return;
    }
    if (!state.practice || state.practice.finished) {
      restorePracticeContent();
      state.practice = {
        round: 1,
        total: PRACTICE_ROUNDS,
        team: 0,
        scores: [0, 0],
        question: null,
        answered: false,
        finished: false
      };
    }
    elements.practicePanel.hidden = false;
    setSteps("practice");
    setAnswerEnabled(false);
    updateScoreboard();
    elements.practicePanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
    if (!state.practice.question) {
      loadPracticeQuestion();
    }
  }

  async function loadPracticeQuestion() {
    if (!state.practice || state.practice.loading) {
      return;
    }
    state.practice.loading = true;
    var requestedPractice = state.practice;
    state.practice.answered = false;
    elements.practiceLoading.hidden = false;
    elements.practiceQuestionBlock.hidden = true;
    elements.practiceError.hidden = true;
    updateScoreboard();

    try {
      var data = await requestJSON("/api/generar_pregunta", {
        method: "POST",
        body: {
          tema: state.topic,
          contexto: state.explanation,
          dificultad: "refuerzo"
        }
      });
      if (!validPracticeQuestion(data)) {
        throw new ApiError("La pregunta llegó incompleta.", "invalid_response");
      }
      if (state.practice !== requestedPractice) {
        return;
      }
      reflectMode(data);
      state.practice.question = data;
      renderPracticeQuestion(data);
    } catch (error) {
      if (state.practice !== requestedPractice) {
        return;
      }
      elements.practiceLoading.hidden = true;
      elements.practiceQuestionBlock.hidden = true;
      elements.practiceError.hidden = false;
      if (isConnectivityIssue(error)) {
        setConnection("offline", error.code === "timeout" ? "Pregunta demorada" : "Conexión intermitente");
      }
    } finally {
      if (state.practice === requestedPractice) {
        state.practice.loading = false;
      }
    }
  }

  function renderPracticeQuestion(data) {
    elements.practiceLoading.hidden = true;
    elements.practiceError.hidden = true;
    elements.practiceQuestionBlock.hidden = false;
    elements.practiceQuestion.textContent = data.pregunta;
    elements.practiceOptions.replaceChildren();
    elements.practiceFeedback.hidden = true;
    elements.practiceFeedback.textContent = "";
    elements.nextQuestionButton.hidden = true;

    data.opciones.forEach(function (option, index) {
      var button = document.createElement("button");
      button.type = "button";
      button.className = "practice-option";
      var letter = document.createElement("span");
      letter.className = "practice-option__letter";
      letter.textContent = String.fromCharCode(65 + index);
      var text = document.createElement("span");
      text.textContent = option;
      button.appendChild(letter);
      button.appendChild(text);
      button.addEventListener("click", function () { answerPractice(index); });
      elements.practiceOptions.appendChild(button);
    });
  }

  function answerPractice(selectedIndex) {
    var practice = state.practice;
    if (!practice || practice.answered || !practice.question) {
      return;
    }
    practice.answered = true;
    var correctIndex = practice.question.respuesta_correcta;
    var isCorrect = selectedIndex === correctIndex;
    var buttons = Array.prototype.slice.call(elements.practiceOptions.children);
    buttons.forEach(function (button, index) {
      button.disabled = true;
      if (index === correctIndex) {
        button.classList.add("is-correct");
      } else if (index === selectedIndex) {
        button.classList.add("is-wrong");
      }
    });

    if (isCorrect) {
      practice.scores[practice.team] += 1;
    }
    updateScoreboard();
    elements.practiceFeedback.hidden = false;
    elements.practiceFeedback.textContent = (isCorrect ? "¡Correcto! " : "Buena conversación. La respuesta correcta es “" + practice.question.opciones[correctIndex] + "”. ") + practice.question.explicacion;
    elements.nextQuestionButton.textContent = practice.round >= practice.total ? "Ver resultado →" : "Siguiente turno →";
    elements.nextQuestionButton.hidden = false;
  }

  function nextPracticeTurn() {
    var practice = state.practice;
    if (!practice || !practice.answered) {
      return;
    }
    if (practice.round >= practice.total) {
      finishPractice();
      return;
    }
    practice.round += 1;
    practice.team = practice.team === 0 ? 1 : 0;
    practice.question = null;
    loadPracticeQuestion();
  }

  function finishPractice() {
    var practice = state.practice;
    practice.finished = true;
    var totalCorrect = practice.scores[0] + practice.scores[1];
    elements.practiceContent.replaceChildren();

    var summary = document.createElement("div");
    summary.className = "practice-summary";
    var icon = document.createElement("span");
    icon.className = "practice-summary__icon";
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = "✓";
    var heading = document.createElement("h4");
    heading.textContent = "Refuerzo completado";
    var paragraph = document.createElement("p");
    paragraph.textContent = "Juntos resolvieron " + totalCorrect + " de " + practice.total + " preguntas. Lo importante fue conversar cada respuesta.";
    var button = createButton("Volver a la tutoría", "button--primary", function () {
      closePractice(true);
    });
    summary.appendChild(icon);
    summary.appendChild(heading);
    summary.appendChild(paragraph);
    summary.appendChild(button);
    elements.practiceContent.appendChild(summary);

    addMessage({
      author: "Actividad de refuerzo",
      text: "Práctica grupal completada: " + totalCorrect + " respuestas correctas de " + practice.total + ".",
      tone: "success"
    });
  }

  function closePractice(completed) {
    elements.practicePanel.hidden = true;
    setSteps(completed || (state.practice && state.practice.finished) ? "practice" : "check");
    setStatus(completed ? "Actividad completada. Puedes comenzar otro tema cuando quieras." : "La actividad queda pausada mientras mantengas esta página abierta.", completed ? "success" : "");
    elements.chat.scrollIntoView({ behavior: "smooth", block: "end" });
  }

  function restoreStudentName() {
    try {
      var storedName = window.localStorage.getItem("manabia_student");
      if (storedName) {
        elements.studentName.value = storedName.slice(0, 40);
      }
    } catch (storageError) {
      // No se requiere almacenamiento local para usar Kosko.
    }
  }

  async function checkServiceMode() {
    if (!navigator.onLine) {
      setConnection("offline", "Navegador sin red");
      return;
    }
    try {
      var data = await requestJSON("/api/estado", { timeout: 5000 });
      reflectMode(data);
    } catch (error) {
      setConnection("offline", "Tutor no disponible");
    }
  }

  var landingScreen = document.getElementById("landingScreen");
  var pageShell = document.getElementById("pageShell");
  var openChatButton = document.getElementById("openChatButton");

  if (openChatButton) {
    openChatButton.addEventListener("click", function () {
      landingScreen.hidden = true;
      pageShell.hidden = false;
      elements.studentName.focus();
    });
  }

  elements.topicSelect.addEventListener("change", function () {
    elements.customTopic.focus();
  });

  elements.topicForm.addEventListener("submit", function (event) {
    event.preventDefault();
    startLearning({ resetChat: true });
  });

  elements.responseForm.addEventListener("submit", function (event) {
    event.preventDefault();
    evaluateAnswer(null, false);
  });

  elements.closePracticeButton.addEventListener("click", function () { closePractice(false); });
  elements.retryPracticeButton.addEventListener("click", loadPracticeQuestion);
  elements.nextQuestionButton.addEventListener("click", nextPracticeTurn);

  window.addEventListener("offline", function () {
    setConnection("offline", "Navegador sin red");
  });
  window.addEventListener("online", checkServiceMode);

  function showWelcomeMessage() {
    if (elements.chat.children.length > 0) {
      return;
    }
    addMessage({
      role: "agent",
      text:
        "Hola, soy Kosko. Cuéntame tu nombre y qué tema quieres aprender hoy, " +
        "y te acompaño paso a paso: te explico, comprobamos que quedó claro y " +
        "practicamos juntos.",
    });
  }

  restoreStudentName();
  checkServiceMode();
  showWelcomeMessage();
})();