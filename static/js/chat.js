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
 * - при ошибке возвращает `false` и показывает alert.
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
        const payload = await response.json();
        if (!response.ok || !payload.ok) {
            alert(payload.error || "Не удалось завершить диалог.");
            return false;
        }
        lockChatUi(payload.dialog_status || "finished");
        return true;
    } catch (error) {
        alert("Ошибка сети при завершении диалога.");
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
            const finished = await finishDialog("timeout");
            if (finished) {
                alert("Время диалога истекло.");
            }
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
        const finished = await finishDialog("manual_feedback");
        if (!finished) {
            finishButton.disabled = false;
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
            const payload = await response.json();
            if (!response.ok || !payload.ok) {
                alert(payload.error || "Не удалось отправить сообщение.");
            } else {
                appendMessage(payload.user_message);
                appendMessage(payload.assistant_message);
                input.value = "";
                scrollToBottom();
            }
        } catch (error) {
            alert("Ошибка сети при отправке сообщения.");
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
