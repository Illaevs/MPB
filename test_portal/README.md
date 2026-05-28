# Nexus Test Portal

Локальный тестовый контур CRM, изолированный от основной базы и основного файлового хранилища.

## Что создаётся

- База данных: `C:\Users\veremyev\Desktop\crm\Новая папка\test_portal\crm_test_portal.db`
- Файловое хранилище: `C:\Users\veremyev\Desktop\crm\Новая папка\test_portal\storage`
- Статика: `C:\Users\veremyev\Desktop\crm\Новая папка\test_portal\static`
- Временные загрузки: `C:\Users\veremyev\Desktop\crm\Новая папка\test_portal\tmp_uploads`

## Важно

- Этот контур **не деплоится на VPS**.
- Основные базы `crm.db` / `crm.db` не используются.
- Все бренды заменены на **Nexus**.

## Тестовые логины

- `admin@nexus-demo.ru` / `Nexus123!`
- `manager@nexus-demo.ru` / `Nexus123!`
- `finance@nexus-demo.ru` / `Nexus123!`
- `contracts@nexus-demo.ru` / `Nexus123!`
- `customer@aurora-demo.ru` / `Nexus123!`
- `customer@vector-demo.ru` / `Nexus123!`
- `geo.lead@testgeo-demo.ru` / `Nexus123!`
- `fire.lead@testfire-demo.ru` / `Nexus123!`
- `hvac.lead@delta-demo.ru` / `Nexus123!`

## Локальный запуск

Backend:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_test_portal_backend.ps1
```

Frontend:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_test_portal_frontend.ps1
```

Или сразу оба:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_test_portal.ps1
```
