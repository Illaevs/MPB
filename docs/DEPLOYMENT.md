# Деплой и эксплуатация (VPS)

Документ описывает текущую схему развёртывания и обслуживания CRM на VPS.

## 1. Доступ и пути

- VPS (текущий): `root@130.49.150.152`
- Проект: `/var/www/www-root/data/www/for-apps.ru/ERPsys`
- Frontend (build): `/var/www/www-root/data/www/for-apps.ru/ERPsys/frontend/dist`
- Backend: `/var/www/www-root/data/www/for-apps.ru/ERPsys/backend`
- SQLite (если используется): `/var/www/www-root/data/www/for-apps.ru/ERPsys/crm.db` (symlink → `/mnt/netdisk/CRM/crm.db`)
- Локальное хранилище файлов (local): `/mnt/netdisk/CRM`

## 2. Systemd сервисы

- `crm-backend.service` — Uvicorn backend.
- `crm-upload-worker.service` — воркер очередей загрузок.
- `crm-notifications-worker.service` — воркер уведомлений.
- `crm-mail-worker.service` (опционально) — воркер синхронизации почты.
- `crm-event-bus-worker.service` — Event Bus v2: outbox-обработка, retry/DLQ, HMAC-подпись подписчикам.
- `crm-embedding-worker.service` — гибридный поиск: вычисление bge-m3 embedding'ов. Нужен только при `ENABLE_HYBRID_SEARCH=1`.

На test-контуре (`mpb-erp.ru` / `130.49.151.237`) аналогичные unit'ы с префиксом `mpb-erp-test-` (`mpb-erp-test-backend.service`, `mpb-erp-test-event-bus-worker.service`, `mpb-erp-test-embedding-worker.service` и т. д.).

Проверка статуса:
```bash
systemctl status crm-backend.service --no-pager -l
systemctl status crm-upload-worker.service --no-pager -l
systemctl status crm-notifications-worker.service --no-pager -l
systemctl status crm-event-bus-worker.service --no-pager -l
systemctl status crm-embedding-worker.service --no-pager -l
```

Логи:
```bash
journalctl -u crm-backend -n 100 --no-pager
journalctl -u crm-upload-worker -n 100 --no-pager
journalctl -u crm-notifications-worker -n 100 --no-pager
journalctl -u crm-event-bus-worker -n 100 --no-pager
journalctl -u crm-embedding-worker -n 100 --no-pager
```

## 3. Обновление backend

1) Собрать архив с нужными файлами:
```bash
tar -czf deploy_backend.tgz backend/app backend/main.py \
  backend/notifications_worker.py backend/upload_worker.py \
  backend/event_outbox_worker.py backend/embedding_worker.py
```

2) Скопировать на VPS и распаковать:
```bash
scp deploy_backend.tgz root@130.49.150.152:/root/
ssh root@130.49.150.152 "cd /var/www/www-root/data/www/for-apps.ru/ERPsys && tar -xzf /root/deploy_backend.tgz"
```

3) Права и перезапуск:
```bash
ssh root@130.49.150.152 "chmod -R a+rX backend/app backend/main.py backend/*worker.py"
ssh root@130.49.150.152 "systemctl restart crm-backend.service crm-upload-worker.service crm-notifications-worker.service crm-event-bus-worker.service crm-embedding-worker.service"
```

## 4. Обновление frontend

1) Build:
```bash
cd frontend
npm run build
```

2) Упаковать `dist`:
```bash
tar -czf deploy_frontend.tgz -C frontend dist
```

3) Скопировать и распаковать:
```bash
scp deploy_frontend.tgz root@130.49.150.152:/root/
ssh root@130.49.150.152 "cd /var/www/www-root/data/www/for-apps.ru/ERPsys/frontend && tar -xzf /root/deploy_frontend.tgz"
ssh root@130.49.150.152 "chmod -R a+rX /var/www/www-root/data/www/for-apps.ru/ERPsys/frontend/dist"
```

## 5. Хранилище (local)

`.env` на backend:
- `STORAGE_BACKEND=local`
- `STORAGE_LOCAL_ROOT=/mnt/netdisk/CRM`

Убедиться, что путь существует и доступен пользователю `www-root`.

Картинки и файлы корпоративной ленты хранятся отдельно от основного storage:
- `<STORAGE_LOCAL_ROOT>/../feed/<uuid>.<ext>` — image-галерея (отдаётся через `/api/v1/feed/image/<filename>`);
- `<STORAGE_LOCAL_ROOT>/../feed-files/<uuid>.<ext>` — произвольные файлы поста (отдаются через `/api/v1/feed/file/<filename>?name=<orig>` с Content-Disposition).

## 5.1 Дополнительные env vars (Hybrid Search и Event Bus)

`.env` на backend для гибридного поиска и шины событий:
- `ENABLE_HYBRID_SEARCH=1` — включает семантический слой поверх FTS5.
- `BGE_M3_MODEL_PATH=/var/.../bge-m3` — путь к локально загруженной модели bge-m3 (1024-dim).
- `EVENT_BUS_HMAC_SECRET=<random-64-bytes>` — секрет для подписи исходящих webhook'ов из Event Bus.

Если `ENABLE_HYBRID_SEARCH` отсутствует / равен `0` — поиск работает только в FTS5-режиме без необходимости в `embedding_worker.service` и модели bge-m3.

## 6. Ограничения загрузки

- Nginx (для `for-apps.ru`): `client_max_body_size 50g`.
- Backend: `UPLOAD_TMP_MAX_BYTES` в `.env` (например, `53687091200` для 50 ГБ).

Проверка в Nginx:
```bash
nginx -T | grep -n "client_max_body_size"
```

## 7. Миграции и скрипты

Примеры запуска ручных скриптов (SQLite):
```bash
ssh root@130.49.150.152 "/var/www/www-root/data/www/for-apps.ru/ERPsys/backend/venv/bin/python /var/www/www-root/data/www/for-apps.ru/ERPsys/backend/create_notification_rules_tables.py"
```

## 8. Быстрые команды

```bash
ssh root@130.49.150.152
cd /var/www/www-root/data/www/for-apps.ru/ERPsys
systemctl restart crm-backend.service crm-upload-worker.service crm-notifications-worker.service \
                  crm-event-bus-worker.service crm-embedding-worker.service
```

## 9. Проверка после деплоя

- Проверить UI и раздел "Файлы".
- Проверить `/api/v1/dashboard/summary` и `/api/v1/notifications/unread-count`.
- Проверить логи systemd (раздел 2).
