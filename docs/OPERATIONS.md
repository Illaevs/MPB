# Operations Runbook

Документ для повседневной эксплуатации CRM в dev/stage/prod средах.

## 1. Scope
- Система: NMBD Tech CRM (`frontend` + `backend` + background workers).
- Основной production-контур:
  - Host: `130.49.150.152`
  - Project root: `/var/www/www-root/data/www/for-apps.ru/ERPsys`
  - Backend: `/var/www/www-root/data/www/for-apps.ru/ERPsys/backend`
  - Frontend build: `/var/www/www-root/data/www/for-apps.ru/ERPsys/frontend/dist`
  - Storage root (local): `/mnt/netdisk/CRM`

## 2. Runtime Components
- API: FastAPI (`backend/main.py`) под systemd `crm-backend.service`.
- Upload worker: `backend/upload_worker.py` под `crm-upload-worker.service`.
- Notifications worker: `backend/notifications_worker.py` под `crm-notifications-worker.service`.
- Mail worker: `backend/mail_worker.py` (systemd unit опционален; если заведён, обычно `crm-mail-worker.service`).
- Reverse proxy: Nginx.

## 3. Operational Commands

### 3.1 Status
```bash
systemctl status crm-backend.service --no-pager -l
systemctl status crm-upload-worker.service --no-pager -l
systemctl status crm-notifications-worker.service --no-pager -l
```

### 3.2 Restart
```bash
systemctl restart crm-backend.service crm-upload-worker.service crm-notifications-worker.service
```

### 3.3 Logs
```bash
journalctl -u crm-backend -n 200 --no-pager
journalctl -u crm-upload-worker -n 200 --no-pager
journalctl -u crm-notifications-worker -n 200 --no-pager
```

### 3.4 Health checks
```bash
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/api/v1/dashboard/summary -H "Authorization: Bearer <TOKEN>"
curl -fsS http://127.0.0.1:8000/api/v1/notifications/unread-count -H "Authorization: Bearer <TOKEN>"
```

## 4. Release Runbook

### 4.1 Pre-flight Checklist
- Проверить свободное место:
```bash
df -h
```
- Проверить, что backend отвечает `/health`.
- Зафиксировать текущие логи ошибок за последние 30 минут.
- Сделать backup БД (раздел 6) перед изменениями схемы/данных.

### 4.2 Backend Release
1. Сформировать пакет:
```bash
tar -czf deploy_backend.tgz backend/app backend/main.py backend/notifications_worker.py backend/upload_worker.py backend/mail_worker.py
```
2. Доставить и распаковать:
```bash
scp deploy_backend.tgz root@130.49.150.152:/root/
ssh root@130.49.150.152 "cd /var/www/www-root/data/www/for-apps.ru/ERPsys && tar -xzf /root/deploy_backend.tgz"
```
3. Выдать права на чтение:
```bash
ssh root@130.49.150.152 "chmod -R a+rX /var/www/www-root/data/www/for-apps.ru/ERPsys/backend"
```
4. Перезапуск:
```bash
ssh root@130.49.150.152 "systemctl restart crm-backend.service crm-upload-worker.service crm-notifications-worker.service"
```

### 4.3 Frontend Release
1. Build:
```bash
cd frontend
npm run build
```
2. Архив:
```bash
tar -czf deploy_frontend.tgz -C frontend dist
```
3. Доставка:
```bash
scp deploy_frontend.tgz root@130.49.150.152:/root/
ssh root@130.49.150.152 "cd /var/www/www-root/data/www/for-apps.ru/ERPsys/frontend && tar -xzf /root/deploy_frontend.tgz"
ssh root@130.49.150.152 "chmod -R a+rX /var/www/www-root/data/www/for-apps.ru/ERPsys/frontend/dist"
```

### 4.4 Post-release Verification
- UI открывается, login работает.
- Проходят smoke-сценарии:
  - список сделок,
  - список задач,
  - уведомления,
  - загрузка файла,
  - открытие раздела файлов.
- Нет свежих критических ошибок в `journalctl` по backend/workers.

## 5. Incident Runbooks

### 5.1 API недоступен
1. Проверить unit:
```bash
systemctl status crm-backend.service --no-pager -l
```
2. Проверить логи:
```bash
journalctl -u crm-backend -n 300 --no-pager
```
3. Проверить `.env` и путь БД.
4. Рестарт `crm-backend.service`.
5. Если не поднялось: rollback последнего deploy-пакета.

### 5.2 Upload queue зависла
Симптомы:
- задачи в `queued`/`processing` не переходят в `done`.
Действия:
1. Проверить `crm-upload-worker.service`.
2. Проверить доступность `STORAGE_LOCAL_ROOT`.
3. Проверить лимиты `UPLOAD_TMP_MAX_BYTES` и заполненность диска.
4. Просмотреть ошибки upload-воркера.
5. После фикса сделать restart upload worker.

### 5.3 Уведомления не приходят
1. Проверить `crm-notifications-worker.service`.
2. Проверить наличие событий в `EventLog`.
3. Проверить активность `NotificationRule`, `NotificationPreference`.
4. Проверить quiet-hours и digest настройки пользователя.

### 5.4 Проблемы с почтой
1. Проверить OAuth-конфиг:
- `YANDEX_OAUTH_CLIENT_ID`
- `YANDEX_OAUTH_CLIENT_SECRET`
- `YANDEX_OAUTH_REDIRECT_URI`
2. Проверить синк (mail worker или ручной запуск).
3. Проверить ошибки SMTP/IMAP в логах backend.

### 5.5 Ошибка доступа к storage
1. Проверить:
- `STORAGE_BACKEND=local`
- `STORAGE_LOCAL_ROOT` существует.
2. Проверить права пользователя сервиса на каталог.
3. Проверить место на диске и inode.

## 6. Backup And Restore

### 6.1 SQLite Backup (online-safe)
```bash
sqlite3 /mnt/netdisk/CRM/crm.db ".backup '/mnt/netdisk/CRM/backups/crm_$(date +%F_%H%M%S).db'"
```

### 6.2 File storage backup
- Рекомендовано регулярное snapshot/rsync каталога `STORAGE_LOCAL_ROOT`.
- Минимум: ежедневный инкремент + еженедельный full.

### 6.3 Restore SQLite
1. Остановить backend и workers:
```bash
systemctl stop crm-backend.service crm-upload-worker.service crm-notifications-worker.service
```
2. Восстановить файл БД из backup.
3. Проверить права на файл.
4. Запустить сервисы.
5. Выполнить smoke checks.

## 7. Data Migrations
- Миграции в проекте выполняются скриптами `create_*.py`/`migrate_*.py`.
- Перед запуском:
  - backup БД обязателен,
  - maintenance window обязателен,
  - фиксируется список выполняемых скриптов.
- После запуска:
  - проверить журналы ошибок,
  - проверить ключевые API (`/health`, `/api/v1/deals`, `/api/v1/tasks`).

## 8. Security Operations
- Ротация секретов:
  - `SECRET_KEY`,
  - OAuth credentials,
  - внешние API токены.
- После ротации:
  - restart backend/workers,
  - проверка login/refresh/OAuth callback.
- Не хранить секреты в markdown, только в `.env`/secret manager.

## 9. Routine Maintenance

### Daily
- Проверка статусов systemd.
- Проверка critical логов за 24ч.
- Проверка свободного места на диске.

### Weekly
- Проверка целостности backup и тестовый restore на непроизводственной среде.
- Ревизия failed upload jobs.

### Monthly
- Ротация/архивация старых логов.
- Ревизия прав доступа к VPS и ключам SSH.
- Проверка Nginx/OS security updates.

## 10. Escalation Template
- Incident id:
- Start time (UTC):
- Affected modules:
- User impact:
- Current status:
- Mitigation:
- Required owner:
- ETA next update:
