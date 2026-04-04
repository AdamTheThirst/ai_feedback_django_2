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
        formData.append("csrfmiddlewaretoken", window.chatConfig.csrfToken);

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
            input.disabled = false;
            button.disabled = false;
            input.focus();
        }
    });

    scrollToBottom();
}

document.addEventListener("DOMContentLoaded", initChatSendForm);
