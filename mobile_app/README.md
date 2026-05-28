# Enterprise Mobile MVP

Flutter-модуль для мобильного MVP системы `Enterprise система управления`.

## Что уже готово

- bearer-token auth под mobile;
- логин через `/api/v1/auth/mobile/login`;
- подтверждение `2FA` через отдельный mobile endpoint;
- базовая домашняя навигация;
- сделки;
- задачи;
- активность и уведомления;
- сводка dashboard;
- платформенные каталоги `android/` и `ios/`.

## Локальная проверка

```bash
flutter pub get
flutter analyze
flutter test
```

## Запуск

По умолчанию приложение смотрит в:

```text
https://mpb-erp.ru
```

При необходимости можно переопределить:

```bash
flutter run --dart-define=API_BASE_URL=https://your-host.example
```

## iOS без Mac

Для iOS в этом репозитории подготовлен cloud-build через `Codemagic`:

- конфиг: [../codemagic.yaml](../codemagic.yaml)
- чеклист: [../docs/IOS_CLOUD_BUILD_TESTFLIGHT.md](../docs/IOS_CLOUD_BUILD_TESTFLIGHT.md)

Основной боевой bundle id:

```text
ru.mpb.erp.mobile
```

## Следующие шаги

1. Добавить refresh-пайплайн на `401`.
2. Вынести агрегированные mobile endpoints (`/mobile/bootstrap`, `/mobile/deals`, `/mobile/tasks`).
3. Подключить push notifications.
4. Подготовить contractor mode и `subrole`-aware screens.
