# Как вернуть оранжевые кнопки (очень простой гайд)

Ниже инструкция «как для ребёнка»: делай шаг за шагом, по порядку.

---

## Почему кнопки стали жёлтыми

Обычно это значит одно из двух:

1. Сайт не подгрузил наш файл стилей `app.css`.
2. Или браузер показывает старую версию CSS из кеша.

В Bootstrap класс `btn-warning` по умолчанию жёлтый.
В нашем проекте он переопределён на оранжевый в файле:

- `static/css/app.css`

---

## Быстрый план

1. Проверить, что в `app.css` реально оранжевый цвет.
2. Обновить статику (`collectstatic`).
3. Перезапустить сервисы.
4. Сбросить кеш браузера.

---

## Шаг 1. Зайди на сервер

```bash
ssh root@ТВОЙ_IP
```

---

## Шаг 2. Открой CSS через nano

```bash
cd /opt/ai_feedback_django_2
nano static/css/app.css
```

Найди блоки `.btn-warning` и `.btn-outline-warning`.

Проверь, что там оранжевые значения (вроде `#ff5400`, `#e24b00`, `#c84200`).

Если нет — поставь такие:

```css
.btn-warning {
    --bs-btn-bg: #ff5400;
    --bs-btn-border-color: #ff5400;
    --bs-btn-color: #fff;
    --bs-btn-hover-bg: #e24b00;
    --bs-btn-hover-border-color: #e24b00;
    --bs-btn-active-bg: #c84200;
    --bs-btn-active-border-color: #c84200;
}

.btn-outline-warning {
    --bs-btn-color: #ff5400;
    --bs-btn-border-color: #ff5400;
    --bs-btn-hover-color: #fff;
    --bs-btn-hover-bg: #ff5400;
    --bs-btn-hover-border-color: #ff5400;
    --bs-btn-active-bg: #e24b00;
    --bs-btn-active-border-color: #e24b00;
}
```

Сохранить в nano:
- `Ctrl + O` → `Enter`
- `Ctrl + X`

---

## Шаг 3. Обнови статику

```bash
cd /opt/ai_feedback_django_2
source .venv/bin/activate
python manage.py collectstatic --noinput
```

---

## Шаг 4. Перезапусти сервисы

```bash
systemctl restart ai_feedback_django_2
systemctl restart nginx
```

Проверь, что всё живо:

```bash
systemctl status ai_feedback_django_2
systemctl status nginx
```

---

## Шаг 5. Очисти кеш браузера

Очень важно: браузер часто держит старый CSS.

Сделай «жёсткое обновление»:

- Windows/Linux: `Ctrl + F5`
- Mac: `Cmd + Shift + R`

Если не помогло — открой сайт в режиме инкогнито.

---

## Если всё ещё жёлтые

Проверь через DevTools:

1. Открой страницу, нажми `F12`.
2. Нажми на жёлтую кнопку.
3. Посмотри, какой CSS победил (`.btn-warning`).
4. Если не видно правил из `app.css`, значит он не подгружается.

Тогда проверь, что в шаблоне подключается:

```html
{% load static %}
<link rel="stylesheet" href="{% static 'css/app.css' %}">
```

И проверь nginx `location /static/` → правильную папку `.../staticfiles/`.

---

## Мини-проверка (чеклист)

- [ ] В `app.css` стоят оранжевые цвета.
- [ ] Выполнен `collectstatic`.
- [ ] Перезапущены `gunicorn`/`nginx`.
- [ ] Сделан hard refresh в браузере.
- [ ] В DevTools видно, что применился `app.css`.

Если все пункты отмечены — кнопки снова будут оранжевые ✅
