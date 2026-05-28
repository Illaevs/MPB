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

Проверка статуса:
```bash
systemctl status crm-backend.service --no-pager -l
systemctl status crm-upload-worker.service --no-pager -l
systemctl status crm-notifications-worker.service --no-pager -l
```

Логи:
```bash
journalctl -u crm-backend -n 100 --no-pager
journalctl -u crm-upload-worker -n 100 --no-pager
journalctl -u crm-notifications-worker -n 100 --no-pager
```

## 3. Обновление backend

1) Собрать архив с нужными файлами:
```bash
tar -czf deploy_backend.tgz backend/app backend/main.py backend/notifications_worker.py backend/upload_worker.py
```

2) Скопировать на VPS и распаковать:
```bash
scp deploy_backend.tgz root@130.49.150.152:/root/
ssh root@130.49.150.152 "cd /var/www/www-root/data/www/for-apps.ru/ERPsys && tar -xzf /root/deploy_backend.tgz"
```

3) Права и перезапуск:
```bash
ssh root@130.49.150.152 "chmod -R a+rX backend/app backend/main.py backend/notifications_worker.py backend/upload_worker.py"
ssh root@130.49.150.152 "systemctl restart crm-backend.service crm-upload-worker.service crm-notifications-worker.service"
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
systemctl restart crm-backend.service crm-upload-worker.service crm-notifications-worker.service
```

## 9. Проверка после деплоя

- Проверить UI и раздел "Файлы".
- Проверить `/api/v1/dashboard/summary` и `/api/v1/notifications/unread-count`.
- Проверить логи systemd (раздел 2).
