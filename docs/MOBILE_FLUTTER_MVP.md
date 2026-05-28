# Flutter Mobile MVP

## Решение

В репозитории создан модуль:

```text
mobile_app/
```

Это не полный `flutter create`-скелет, а бизнесовой стартовый каркас:
- auth через bearer token;
- базовая домашняя навигация;
- dashboard summary;
- сделки;
- задачи;
- уведомления/активность;
- проверка AI status.

## Платформенные папки

Платформенные папки уже сгенерированы:
- `mobile_app/ios/` — нативный Runner для iOS, конфигурации сборки см. в `docs/IOS_CLOUD_BUILD_TESTFLIGHT.md`;
- `mobile_app/android/` — Gradle-проект для Android.

CI/сборка iOS-релизов выполняется через Codemagic (`codemagic.yaml` в корне). Локально для разработки достаточно установить Flutter SDK + Xcode (iOS) / Android Studio (Android) и запустить `flutter run` из `mobile_app/`.

## Backend-опора

Добавлены mobile-friendly auth endpoints:

- `POST /api/v1/auth/mobile/login`
- `POST /api/v1/auth/mobile/verify-2fa`
- `POST /api/v1/auth/mobile/refresh`

Они возвращают bearer tokens и позволяют Flutter не зависеть от web cookie-session.

## Текущий набор используемых endpoint'ов

- `GET /api/v1/dashboard/summary`
- `GET /api/v1/deals`
- `GET /api/v1/tasks`
- `GET /api/v1/notifications`
- `GET /api/v1/ai/status`

## Следующий backend этап

Нужно добавить компактные mobile endpoints:

- `GET /api/v1/mobile/bootstrap`
- `GET /api/v1/mobile/deals`
- `GET /api/v1/mobile/deals/{id}`
- `GET /api/v1/mobile/tasks`
- `GET /api/v1/mobile/activity`

Их задача — отдавать уже собранные DTO под роли, а не заставлять mobile повторять web-агрегацию.

## Следующий frontend/mobile этап

1. contractor mode через `subrole + linked_company`;
2. нормальный refresh token flow на `401`;
3. проектная карточка mobile;
4. чат/уведомления/push;
5. файловые сценарии;
6. AI assistant quick-actions.

