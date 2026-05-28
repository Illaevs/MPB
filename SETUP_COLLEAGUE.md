# Инструкция По Разворачиванию

Документ для коллеги, который получает sanitized-копию проекта без реальных БД, чатов, контрагентов и брендовых данных.

## Что В Архиве

- backend: FastAPI + SQLAlchemy
- frontend: Vue 3 + Vite
- docs: внутренняя документация
- scripts: скрипты запуска и bootstrap demo-контура

В архив **не входят**:

- реальные БД
- `.env`
- `storage`, `test_portal`, временные загрузки
- бинарные шаблоны и офисные файлы, которые могли содержать реальные данные

## Рекомендуемое Окружение

- Windows 10/11 + PowerShell
- Python `3.10` или `3.11` или `3.12`
- Node.js `20 LTS`
- npm `10+`

Linux/macOS тоже возможны, но команды ниже приведены для Windows PowerShell.

## Что Ставить

### Backend

Все Python-зависимости ставятся одной командой из файла:

- `backend/requirements.txt`

Основные пакеты:

- `fastapi`
- `uvicorn[standard]`
- `sqlalchemy`
- `aiosqlite`
- `psycopg2-binary`
- `asyncpg`
- `python-multipart`
- `PyJWT[crypto]`
- `bcrypt`
- `python-decouple`
- `pydantic`
- `pydantic-settings`
- `email-validator`
- `pandas`
- `numpy`
- `httpx`
- `xhtml2pdf`
- `redis`
- `num2words`

### Frontend

Все JS-зависимости ставятся через `npm install` в папке `frontend`.

Основные пакеты:

- `vue`
- `vite`
- `pinia`
- `vue-router`
- `axios`
- `apexcharts`
- `vue3-apexcharts`
- `dhtmlx-gantt`
- `dompurify`
- `driver.js`
- `docxtemplater`
- `docx-preview`
- `file-saver`
- `qrcode`
- `vuedraggable`

## Самый Простой Способ Запуска

Рекомендуемый сценарий: **demo/test portal**.

Почему так:

- он не требует продовой БД;
- сам создает отдельную локальную тестовую БД;
- сам создает отдельное локальное файловое хранилище;
- в нем уже есть тестовые пользователи, роли, сделки и документы.

### 1. Распаковать архив

Например:

```powershell
cd C:\Work
Expand-Archive .\crm-sanitized-*.zip -DestinationPath .\crm-sanitized
cd .\crm-sanitized
```

### 2. Поставить frontend-зависимости

```powershell
cd frontend
npm install
cd ..
```

### 3. Поднять demo-контур

Один запуск обоих процессов:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_test_portal.ps1
```

Или по отдельности:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_test_portal_backend.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\start_test_portal_frontend.ps1
```

### Что происходит автоматически

- создается виртуальное окружение: `.\.venvs\test_portal`
- ставятся backend-библиотеки из `backend/requirements.txt`
- создается отдельная БД: `.\test_portal\crm_test_portal.db`
- создаются тестовые storage/static/tmp папки внутри `.\test_portal`

### Адреса

- frontend: [http://127.0.0.1:3001](http://127.0.0.1:3001)
- backend: [http://127.0.0.1:8001](http://127.0.0.1:8001)
- health: [http://127.0.0.1:8001/health](http://127.0.0.1:8001/health)

### Тестовые логины

- `admin@nexus-demo.ru` / `Nexus123!`
- `manager@nexus-demo.ru` / `Nexus123!`
- `finance@nexus-demo.ru` / `Nexus123!`
- `contracts@nexus-demo.ru` / `Nexus123!`
- `customer@aurora-demo.ru` / `Nexus123!`
- `customer@vector-demo.ru` / `Nexus123!`

## Ручной Запуск Без Demo-Портала

Этот сценарий нужен, если хочется просто поднять backend/frontend на чистой локальной SQLite-базе.

Важно:

- приложение стартует;
- SQLite-файл можно создать отдельно;
- но без сидов/ролей/пользователей логиниться будет некуда;
- поэтому для первого знакомства все равно лучше demo/test portal.

### 1. Создать Python venv

```powershell
python -m venv .\.venvs\backend
.\.venvs\backend\Scripts\python.exe -m pip install --upgrade pip
.\.venvs\backend\Scripts\python.exe -m pip install -r .\backend\requirements.txt
```

### 2. Задать переменные окружения для backend

Пример для PowerShell:

```powershell
$env:SECRET_KEY = 'replace-with-very-long-local-secret-key-min-64-symbols-1234567890'
$env:SQLALCHEMY_DATABASE_URI = 'sqlite:///C:/Work/crm-sanitized/local_dev.db'
$env:AUTH_COOKIE_SECURE = 'false'
$env:REQUIRE_TWO_FACTOR = 'false'
$env:APP_HOST = '127.0.0.1'
$env:APP_PORT = '8000'
$env:APP_RELOAD = 'true'
$env:REDIS_URL = ''
```

Примечания:

- `SECRET_KEY` обязателен и должен быть длиной не меньше 64 символов.
- `REQUIRE_TWO_FACTOR=false` удобнее для локальной разработки.
- `AUTH_COOKIE_SECURE=false` обязателен для обычного локального `http`.
- `REDIS_URL` можно оставить пустым для локального старта.

### 3. Запустить backend

```powershell
cd backend
..\.venvs\backend\Scripts\python.exe .\run.py
```

### 4. Поставить frontend-зависимости

```powershell
cd ..\frontend
npm install
```

### 5. Настроить frontend proxy

Создать файл `frontend/.env.local` со значениями:

```env
VITE_DEV_PORT=3000
VITE_API_PROXY_TARGET=http://127.0.0.1:8000
VITE_APP_BRAND_NAME=Nexus
VITE_APP_BRAND_SUFFIX=
VITE_APP_SYSTEM_NAME=Nexus
VITE_APP_CRM_NAME=Nexus CRM
```

### 6. Запустить frontend

```powershell
npm run dev -- --host 127.0.0.1 --strictPort
```

## Что Не Обязательно Для Локального Старта

Можно не настраивать сразу:

- PostgreSQL
- Redis
- Yandex OAuth
- SMTP/IMAP
- Telegram bot
- DaData

Базовый локальный demo-контур работает без них.

## Что Важно Понимать

### 1. Root package.json

В корне есть `package.json`, но для обычного запуска приложения он не нужен.

Для старта достаточно:

- `backend/requirements.txt`
- `frontend/package.json`

### 2. Пустая база и demo-база

- demo/test portal: отдельная готовая тестовая БД с данными
- ручной пустой запуск: база будет пустая, без нормального первого входа

### 3. Продовая БД не нужна

Ни один из рекомендуемых сценариев не требует продовую БД.

## Типичные Проблемы

### PowerShell блокирует запуск `.ps1`

Запускать так:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_test_portal.ps1
```

### Порт занят

Проверить:

- backend: `8001` для demo или `8000` для ручного запуска
- frontend: `3001` для demo или `3000` для ручного запуска

При необходимости поменять:

- `frontend/.env.testportal`
- `frontend/.env.local`
- переменные `APP_PORT` / `VITE_DEV_PORT`

### Не ставятся npm пакеты

Проверить версии:

```powershell
node -v
npm -v
```

Рекомендуется `Node 20 LTS`.

### Не стартует backend из-за SECRET_KEY

Это ожидаемо. В проекте есть защита:

- `SECRET_KEY` нельзя оставлять дефолтным
- нужен свой локальный ключ длиной `64+`

## Что Лучше Передать Коллеге

Минимальный удобный набор:

1. сам sanitized zip;
2. этот файл `SETUP_COLLEAGUE.md`;
3. короткую пометку: “рекомендуемый запуск через `scripts/start_test_portal.ps1`”.
