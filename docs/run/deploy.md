# deploy.md

# Простой деплой на VPS (очень понятная инструкция)

> Этот файл написан простыми словами.
> Цель: чтобы даже ребёнок мог повторить шаги по порядку.

---

## 1) Какие данные нужны, чтобы поставить проект на свой VPS?

Минимальный набор:

1. **IP сервера** (пример: `123.45.67.89`).
2. **Логин для входа по SSH** (обычно `root` или другой пользователь).
3. **Пароль или SSH-ключ** для входа на сервер.
4. **Домен** (не обязательно, но лучше иметь).
5. **Репозиторий проекта** (ссылка Git).
6. **Секреты для `.env`**:
   - `SECRET_KEY`
   - `ALLOWED_HOSTS`
   - параметры LLM (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL_NAME`)
   - email-настройки (если нужны отправки писем)
7. Понимание, где будет храниться проект на сервере (например `/opt/ai_feedback_django_2`).

Если коротко: **IP + доступ по SSH + репозиторий + `.env` значения**.

---

## 2) Что нужно поменять в проекте перед релизом на VPS?

Перед запуском в проде проверь это обязательно:

1. **Выключить debug**:
   - `DEBUG=False`.
2. **Указать правильные хосты**:
   - `ALLOWED_HOSTS=твой_ip,твой_домен`.
3. **Поставить production settings**:
   - `DJANGO_SETTINGS_MODULE=config.settings.production`.
4. **Сменить секретный ключ**:
   - `SECRET_KEY` должен быть длинным и новым.
5. **Настроить статику**:
   - выполнить `collectstatic`.
6. **Прогнать миграции**:
   - выполнить `migrate`.
7. **Проверить LLM параметры**:
   - правильный `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL_NAME`.
8. **Проверить безопасность сервера**:
   - открыть только нужные порты (обычно 22, 80, 443).
9. **Запускать через gunicorn + nginx**, а не через `runserver`.

---

## 3) Пошагово: что сделать, чтобы всё заработало

Ниже пошагово, как по рецепту.

### Шаг 0. Подключись к серверу

На своём компьютере открой терминал:

```bash
ssh root@ТВОЙ_IP
```

---

### Шаг 1. Установи нужные программы

```bash
apt update && apt upgrade -y
apt install -y python3 python3-venv python3-pip git nginx
```

---

### Шаг 2. Скопируй проект

```bash
mkdir -p /opt
cd /opt
git clone <URL_РЕПОЗИТОРИЯ> ai_feedback_django_2
cd ai_feedback_django_2
```

---

### Шаг 3. Создай виртуальное окружение и поставь зависимости

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Шаг 4. Создай `.env`

```bash
cp .env.example .env
nano .env
```

Минимально проверь в `.env`:

```env
DJANGO_SETTINGS_MODULE=config.settings.production
DEBUG=False
SECRET_KEY=ОЧЕНЬ_ДЛИННЫЙ_УНИКАЛЬНЫЙ_КЛЮЧ
ALLOWED_HOSTS=ТВОЙ_IP,ТВОЙ_ДОМЕН
```

И добавь актуальные параметры LLM/email из своего окружения.

---

### Шаг 5. Подготовь базу и статику

```bash
source .venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

---

### Шаг 6. Проверь, что Django стартует

```bash
source .venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

Открой `http://ТВОЙ_IP:8000`.
Если всё работает — останови `Ctrl + C`.

---

### Шаг 7. Запусти через Gunicorn

```bash
source .venv/bin/activate
pip install gunicorn
gunicorn config.wsgi:application --bind 127.0.0.1:8000
```

Если стартовал — останови `Ctrl + C`.

---

### Шаг 8. Сделай systemd-сервис

```bash
nano /etc/systemd/system/ai_feedback_django_2.service
```

Вставь:

```ini
[Unit]
Description=ai_feedback_django_2 gunicorn
After=network.target

[Service]
User=root
WorkingDirectory=/opt/ai_feedback_django_2
EnvironmentFile=/opt/ai_feedback_django_2/.env
ExecStart=/opt/ai_feedback_django_2/.venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Дальше:

```bash
systemctl daemon-reload
systemctl enable ai_feedback_django_2
systemctl start ai_feedback_django_2
systemctl status ai_feedback_django_2
```

---

### Шаг 9. Настрой Nginx

```bash
nano /etc/nginx/sites-available/ai_feedback_django_2
```

Вставь:

```nginx
server {
    listen 80;
    server_name _;

    location /static/ {
        alias /opt/ai_feedback_django_2/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Включи и перезапусти:

```bash
ln -s /etc/nginx/sites-available/ai_feedback_django_2 /etc/nginx/sites-enabled/ai_feedback_django_2
nginx -t
systemctl restart nginx
```

---

## 3.1) Если есть только IP

Тогда делай так:

1. В `.env` поставь:
   - `ALLOWED_HOSTS=ТВОЙ_IP`
2. В nginx оставь:
   - `server_name _;`
3. Открывай сайт через:
   - `http://ТВОЙ_IP`

Это рабочий вариант без домена.

---

## 3.2) Если есть домен третьего уровня

Пример домена 3-го уровня: `app.example.com`.

Сделай так:

1. У регистратора домена создай **A-запись**:
   - `app.example.com -> ТВОЙ_IP`
2. В `.env`:
   - `ALLOWED_HOSTS=app.example.com,ТВОЙ_IP`
3. В nginx:
   - `server_name app.example.com;`
4. (Рекомендуется) поставить HTTPS через certbot:

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d app.example.com
```

После этого сайт лучше открывать по `https://app.example.com`.

---

## 4) Как запустить

После первой настройки:

```bash
systemctl start ai_feedback_django_2
systemctl restart ai_feedback_django_2
systemctl status ai_feedback_django_2
systemctl restart nginx
```

Если менял код:

```bash
cd /opt/ai_feedback_django_2
git pull
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
systemctl restart ai_feedback_django_2
systemctl restart nginx
```

---

## 5) Вопросы про VENV, БД и `.env`

### 5.1 Можно ли скопировать готовый VENV на VPS?

**Лучше не надо.**

Почему:
- venv часто «привязан» к другой системе и путям;
- на другом сервере может сломаться.

Правильнее:
1. создать новый `.venv` на VPS;
2. установить зависимости через `pip install -r requirements.txt`.

---

### 5.2 Можно ли просто скопировать БД вместо миграций?

Для **SQLite** технически можно скопировать файл БД, но:
- безопаснее и правильнее на чистом сервере сделать `migrate`;
- перенос файла БД — это уже отдельная операция (например, для переноса реальных данных).

Рекомендация:
1. новый сервер -> сначала `migrate`;
2. если нужно перенести старые данные -> делай бэкап/restore отдельно.

---

### 5.3 `.env` оставлять файлом или прописывать в bash?

Можно и так, и так.

Самый простой и понятный вариант:
- держать `.env` файлом в папке проекта;
- в systemd указать `EnvironmentFile=/opt/ai_feedback_django_2/.env`.

Это удобно: открыл `.env`, поправил, перезапустил сервис.

---

## Очень короткая памятка

1. Зашёл на VPS.
2. Склонировал проект.
3. Создал `.venv`.
4. Поставил зависимости.
5. Заполнил `.env`.
6. `migrate` + `collectstatic`.
7. Запустил gunicorn как сервис.
8. Настроил nginx.
9. Проверил сайт в браузере.

Готово ✅
