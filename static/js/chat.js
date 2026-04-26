"use strict";

/**
 * Возвращает UUID v4 для idempotency-ключа клиентской отправки.
 *
 * Контекст использования:
 * - применяется при каждой отправке сообщения для защиты от дублей в API.
 *
 * Параметры:
 * - отсутствуют.
 *
 * Возвращает:
 * - строковый UUID v4.
 *
 * Исключения и особые случаи:
 * - отсутствуют.
 *
 * Побочные эффекты:
 * - отсутствуют.
 */
function generateUuidV4() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (char) {
        const random = (Math.random() * 16) | 0;
        const value = char === "x" ? random : (random & 0x3) | 0x8;
        return value.toString(16);
    });
}

/**
 * Добавляет сообщение в DOM-ленту чата.
 *
 * Контекст использования:
 * - вызывается после успешной отправки и получения JSON-ответа.
 *
 * Параметры:
 * - `message`: объект сообщения с полями `role` и `text`.
 *
 * Возвращает:
 * - отсутствует.
 *
 * Исключения и особые случаи:
 * - если сообщение отсутствует, функция завершает работу без изменений.
 *
 * Побочные эффекты:
 * - модифицирует DOM списка сообщений.
 */
function appendMessage(message) {
    if (!message) {
        return;
    }
    const list = document.getElementById("message-list");
    const row = document.createElement("div");
    row.className = `message-row ${message.role === "user" ? "message-user" : "message-assistant"}`;

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.textContent = message.text;

    row.appendChild(bubble);
    list.appendChild(row);
}

/**
 * Управляет видимостью overlay окна ожидания анализа.
 *
 * Контекст использования:
 * - включается после клика «Дай обратную связь» на время серверного завершения/анализа.
 *
 * Параметры:
 * - `isVisible`: `true` — показать overlay, `false` — скрыть.
 *
 * Возвращает:
 * - отсутствует.
 *
 * Исключения и особые случаи:
 * - если overlay-элемент не найден, функция ничего не делает.
 *
 * Побочные эффекты:
 * - изменяет классы и `aria-hidden` у `#analysis-overlay`.
 */
function setAnalysisOverlayVisible(isVisible) {
    const overlay = document.getElementById("analysis-overlay");
    if (!overlay) {
        return;
    }
    if (isVisible) {
        overlay.classList.remove("d-none");
        overlay.setAttribute("aria-hidden", "false");
    } else {
        overlay.classList.add("d-none");
        overlay.setAttribute("aria-hidden", "true");
    }
}

/**
 * Обновляет подпись прогресса аналитики в формате `m из n`.
 *
 * Контекст использования:
 * - вызывается во время polling endpoint-а прогресса анализа;
 * - отображает пользователю, сколько промтов уже обработано.
 *
 * Параметры:
 * - `completedCount`: количество уже обработанных промтов;
 * - `totalCount`: общее количество промтов.
 *
 * Возвращает:
 * - отсутствует.
 *
 * Исключения и особые случаи:
 * - если элемент подписи не найден, функция ничего не делает.
 *
 * Побочные эффекты:
 * - меняет текст узла `#analysis-progress-text`.
 */
function setAnalysisProgressText(completedCount, totalCount) {
    const node = document.getElementById("analysis-progress-text");
    if (!node) {
        return;
    }
    const completed = Math.max(parseInt(completedCount || 0, 10), 0);
    const total = Math.max(parseInt(totalCount || 0, 10), 0);
    node.textContent = `${completed} из ${total}`;
}

/**
 * Запускает polling серверного прогресса анализа.
 *
 * Контекст использования:
 * - включается при ручном завершении диалога;
 * - позволяет обновлять подпись `m из n` до редиректа на страницу результатов.
 *
 * Параметры:
 * - отсутствуют.
 *
 * Возвращает:
 * - идентификатор интервала `setInterval` или `null`, если polling недоступен.
 *
 * Исключения и особые случаи:
 * - при сетевых ошибках тихо пропускает тик, не прерывая поток.
 *
 * Побочные эффекты:
 * - выполняет периодические GET-запросы к `progressUrl`.
 */
function startAnalysisProgressPolling() {
    if (!window.chatConfig || !window.chatConfig.progressUrl) {
        return null;
    }
    const intervalId = setInterval(async function () {
        try {
            const response = await fetch(window.chatConfig.progressUrl, {
                method: "GET",
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                }
            });
            const parsed = await safeReadJson(response);
            if (!parsed.ok || !parsed.payload || !parsed.payload.ok) {
                return;
            }
            setAnalysisProgressText(parsed.payload.completed_count, parsed.payload.total_count);
        } catch (error) {
            return;
        }
    }, 700);
    return intervalId;
}

/**
 * Прокручивает ленту сообщений к последней реплике.
 *
 * Контекст использования:
 * - применяется после добавления сообщений и при загрузке экрана.
 *
 * Параметры:
 * - отсутствуют.
 *
 * Возвращает:
 * - отсутствует.
 *
 * Исключения и особые случаи:
 * - если контейнер не найден, функция завершает выполнение.
 *
 * Побочные эффекты:
 * - изменяет позицию прокрутки контейнера сообщений.
 */
function scrollToBottom() {
    const area = document.getElementById("messages-scroll-area");
    if (!area) {
        return;
    }
    area.scrollTop = area.scrollHeight;
}

/**
 * Возвращает csrf-токен для POST-запросов.
 *
 * Контекст использования:
 * - используется для обычных AJAX-вызовов, где действует стандартная CSRF-проверка.
 *
 * Параметры:
 * - отсутствуют.
 *
 * Возвращает:
 * - строку CSRF-токена.
 *
 * Исключения и особые случаи:
 * - если токен отсутствует, возвращается пустая строка.
 *
 * Побочные эффекты:
 * - отсутствуют.
 */
function getCsrfToken() {
    return (window.chatConfig && window.chatConfig.csrfToken) || "";
}

/**
 * Пытается безопасно извлечь JSON из HTTP-ответа.
 *
 * Контекст использования:
 * - применяется в API-запросах чата и завершения диалога;
 * - защищает клиент от падения при HTML-ошибках (например, 403/500).
 *
 * Параметры:
 * - `response`: объект `Response` из `fetch`.
 *
 * Возвращает:
 * - объект с полями:
 *   - `ok`: удалось ли разобрать JSON;
 *   - `payload`: распарсенный JSON или `null`;
 *   - `rawText`: сырой текст ответа.
 *
 * Исключения и особые случаи:
 * - при не-JSON контенте вернёт `ok=false` и текст ответа.
 *
 * Побочные эффекты:
 * - отсутствуют.
 */
async function safeReadJson(response) {
    const rawText = await response.text();
    try {
        return {
            ok: true,
            payload: JSON.parse(rawText),
            rawText: rawText
        };
    } catch (error) {
        return {
            ok: false,
            payload: null,
            rawText: rawText
        };
    }
}

/**
 * Отображает нейтральное статусное сообщение внизу окна чата.
 *
 * Контекст использования:
 * - заменяет браузерные `alert` при ошибках сети/валидации и технических событиях.
 *
 * Параметры:
 * - `text`: текст статуса для пользователя.
 *
 * Возвращает:
 * - отсутствует.
 *
 * Исключения и особые случаи:
 * - если DOM-элемент отсутствует, функция ничего не делает.
 *
 * Побочные эффекты:
 * - обновляет текст узла `#chat-status-line`.
 */
function setChatStatusLine(text) {
    const node = document.getElementById("chat-status-line");
    if (!node) {
        return;
    }
    node.textContent = text || "";
}

/**
 * Переводит интерфейс в состояние «диалог завершён».
 *
 * Контекст использования:
 * - вызывается после ручного завершения, таймаута или сигнала ухода со страницы.
 *
 * Параметры:
 * - `status`: финальный серверный статус диалога.
 *
 * Возвращает:
 * - отсутствует.
 *
 * Исключения и особые случаи:
 * - отсутствуют.
 *
 * Побочные эффекты:
 * - блокирует поле ввода и кнопки отправки/завершения.
 */
function lockChatUi(status) {
    const input = document.getElementById("chat-input");
    const sendButton = document.getElementById("chat-send-button");
    const finishButton = document.getElementById("dialog-finish-button");

    if (input) {
        input.disabled = true;
    }
    if (sendButton) {
        sendButton.disabled = true;
    }
    if (finishButton) {
        finishButton.disabled = true;
    }
    if (window.chatConfig) {
        window.chatConfig.dialogStatus = status;
    }
}

/**
 * Форматирует секунды в вид `MM:SS`.
 *
 * Контекст использования:
 * - применяется для визуализации обратного отсчёта на экране чата.
 *
 * Параметры:
 * - `seconds`: количество секунд.
 *
 * Возвращает:
 * - строку в формате `MM:SS`.
 *
 * Исключения и особые случаи:
 * - отрицательные значения интерпретируются как `00:00`.
 *
 * Побочные эффекты:
 * - отсутствуют.
 */
function formatTimerValue(seconds) {
    const safeSeconds = Math.max(parseInt(seconds || 0, 10), 0);
    const minutes = Math.floor(safeSeconds / 60);
    const rest = safeSeconds % 60;
    return `${String(minutes).padStart(2, "0")}:${String(rest).padStart(2, "0")}`;
}

/**
 * Завершает диалог через JSON-endpoint с указанной причиной.
 *
 * Контекст использования:
 * - общий вызов для кнопки ручного завершения и автозавершения по таймеру.
 *
 * Параметры:
 * - `reason`: код причины (`manual_feedback` или `timeout`).
 *
 * Возвращает:
 * - Promise с `true`, если сервер подтвердил завершение.
 *
 * Исключения и особые случаи:
 * - при ошибке возвращает `false` и выводит нейтральный текстовый статус.
 *
 * Побочные эффекты:
 * - блокирует UI при успешном завершении.
 */
async function finishDialog(reason) {
    if (!window.chatConfig || window.chatConfig.dialogStatus !== "active") {
        return true;
    }

    const formData = new FormData();
    formData.append("reason", reason);
    formData.append("csrfmiddlewaretoken", getCsrfToken());

    try {
        const response = await fetch(window.chatConfig.finishUrl, {
            method: "POST",
            body: formData,
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            }
        });
        const parsed = await safeReadJson(response);
        if (!parsed.ok) {
            setChatStatusLine(`Сервер вернул некорректный ответ (${response.status}). Проверьте логи.`);
            setAnalysisOverlayVisible(false);
            return false;
        }
        const payload = parsed.payload;
        if (!response.ok || !payload.ok) {
            setChatStatusLine(payload.error || `Не удалось завершить диалог (HTTP ${response.status}).`);
            setAnalysisOverlayVisible(false);
            return false;
        }
        setChatStatusLine("");
        lockChatUi(payload.dialog_status || "finished");
        if (window.chatConfig.resultsUrl) {
            window.location.href = window.chatConfig.resultsUrl;
        }
        return true;
    } catch (error) {
        setChatStatusLine("Ошибка сети при завершении диалога.");
        setAnalysisOverlayVisible(false);
        return false;
    }
}

/**
 * Отправляет сигнал ухода со страницы через `sendBeacon` и fallback-запрос.
 *
 * Контекст использования:
 * - вызывается в `pagehide`, чтобы не потерять завершение сессии при закрытии вкладки.
 *
 * Параметры:
 * - отсутствуют.
 *
 * Возвращает:
 * - отсутствует.
 *
 * Исключения и особые случаи:
 * - если диалог уже завершён, запрос не отправляется.
 *
 * Побочные эффекты:
 * - отправляет POST-запрос на endpoint `page_leave`.
 */
function sendPageLeaveSignal() {
    if (!window.chatConfig || window.chatConfig.dialogStatus !== "active") {
        return;
    }

    const beaconData = new FormData();
    beaconData.append("reason", "page_leave");

    let delivered = false;
    if (navigator.sendBeacon) {
        delivered = navigator.sendBeacon(window.chatConfig.pageLeaveUrl, beaconData);
    }

    if (!delivered) {
        fetch(window.chatConfig.pageLeaveUrl, {
            method: "POST",
            body: beaconData,
            keepalive: true,
            credentials: "same-origin",
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            }
        }).catch(function () {
            return null;
        });
    }
}

/**
 * Инициализирует клиентский таймер и автозавершение по истечении времени.
 *
 * Контекст использования:
 * - запускается при открытии чатового экрана.
 *
 * Параметры:
 * - отсутствуют.
 *
 * Возвращает:
 * - отсутствует.
 *
 * Исключения и особые случаи:
 * - если таймерный элемент отсутствует, функция завершается без действий.
 *
 * Побочные эффекты:
 * - обновляет таймер в DOM и вызывает `finishDialog('timeout')` при нуле.
 */
function initDialogTimer() {
    const timerNode = document.getElementById("chat-timer");
    if (!timerNode || !window.chatConfig) {
        return;
    }

    let secondsRemaining = parseInt(window.chatConfig.secondsRemaining || 0, 10);
    timerNode.textContent = formatTimerValue(secondsRemaining);

    const timerId = setInterval(async function () {
        if (window.chatConfig.dialogStatus !== "active") {
            clearInterval(timerId);
            return;
        }
        secondsRemaining = Math.max(secondsRemaining - 1, 0);
        timerNode.textContent = formatTimerValue(secondsRemaining);

        if (secondsRemaining === 0) {
            clearInterval(timerId);
            await finishDialog("timeout");
        }
    }, 1000);
}

/**
 * Инициализирует обработчик кнопки «Дай обратную связь».
 *
 * Контекст использования:
 * - позволяет пользователю завершить сценарий вручную.
 *
 * Параметры:
 * - отсутствуют.
 *
 * Возвращает:
 * - отсутствует.
 *
 * Исключения и особые случаи:
 * - если кнопка отсутствует, обработчик не регистрируется.
 *
 * Побочные эффекты:
 * - вызывает серверное завершение диалога и блокирует UI.
 */
function initManualFinishButton() {
    const finishButton = document.getElementById("dialog-finish-button");
    if (!finishButton) {
        return;
    }

    finishButton.addEventListener("click", async function () {
        finishButton.disabled = true;
        setAnalysisOverlayVisible(true);
        setAnalysisProgressText(0, 0);
        const progressIntervalId = startAnalysisProgressPolling();
        const finished = await finishDialog("manual_feedback");
        if (progressIntervalId) {
            clearInterval(progressIntervalId);
        }
        if (!finished) {
            finishButton.disabled = false;
            setAnalysisOverlayVisible(false);
        }
    });
}

/**
 * Инициализирует отправку сообщений в JSON-endpoint без перезагрузки страницы.
 *
 * Контекст использования:
 * - запускается на DOMContentLoaded для чатового экрана.
 *
 * Параметры:
 * - отсутствуют.
 *
 * Возвращает:
 * - отсутствует.
 *
 * Исключения и особые случаи:
 * - если чатовая форма отсутствует на странице, функция ничего не делает.
 *
 * Побочные эффекты:
 * - подписывает обработчик `submit`;
 * - выполняет сетевые запросы и управляет состоянием кнопки/индикатора.
 */
function initChatSendForm() {
    const form = document.getElementById("chat-send-form");
    if (!form) {
        return;
    }

    const input = document.getElementById("chat-input");
    const button = document.getElementById("chat-send-button");
    const typingIndicator = document.getElementById("typing-indicator");

    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        const text = (input.value || "").trim();
        if (!text) {
            return;
        }

        appendMessage({role: "user", text: text});
        input.value = "";
        scrollToBottom();

        input.disabled = true;
        button.disabled = true;
        typingIndicator.classList.remove("d-none");

        const formData = new FormData();
        formData.append("text", text);
        formData.append("client_message_id", generateUuidV4());
        formData.append("csrfmiddlewaretoken", getCsrfToken());

        try {
            const response = await fetch(window.chatConfig.sendUrl, {
                method: "POST",
                body: formData,
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                }
            });
            const parsed = await safeReadJson(response);
            if (!parsed.ok) {
                setChatStatusLine(`Сервер вернул некорректный ответ (${response.status}). Проверьте логи.`);
            } else if (!response.ok || !parsed.payload.ok) {
                setChatStatusLine(parsed.payload.error || `Не удалось отправить сообщение (HTTP ${response.status}).`);
            } else {
                appendMessage(parsed.payload.assistant_message);
                setChatStatusLine("");
                scrollToBottom();
            }
        } catch (error) {
            setChatStatusLine("Ошибка сети при отправке сообщения.");
        } finally {
            typingIndicator.classList.add("d-none");
            if (window.chatConfig.dialogStatus === "active") {
                input.disabled = false;
                button.disabled = false;
                input.focus();
            }
        }
    });

    scrollToBottom();
}

/**
 * Инициализирует обработчики экрана чата после загрузки DOM.
 *
 * Контекст использования:
 * - единая точка запуска для всех клиентских модулей страницы.
 *
 * Параметры:
 * - отсутствуют.
 *
 * Возвращает:
 * - отсутствует.
 *
 * Исключения и особые случаи:
 * - отсутствуют.
 *
 * Побочные эффекты:
 * - подписывает обработчики на события окна и формы.
 */
function initChatPage() {
    initChatSendForm();
    initManualFinishButton();
    initDialogTimer();
    window.addEventListener("pagehide", sendPageLeaveSignal);
}

document.addEventListener("DOMContentLoaded", initChatPage);
