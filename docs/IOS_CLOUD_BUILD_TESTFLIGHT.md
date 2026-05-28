# iOS cloud build и TestFlight без локального Mac

Этот проект подготовлен под сборку iOS через `Codemagic` без собственного Mac.

## Что уже зафиксировано в репозитории

- Flutter-проект: [mobile_app](c:\Users\veremyev\Desktop\crm\Новая%20папка\mobile_app)
- Codemagic config: [codemagic.yaml](c:\Users\veremyev\Desktop\crm\Новая%20папка\codemagic.yaml)
- iOS bundle id: `ru.mpb.erp.mobile`
- Android application id: `ru.mpb.erp.mobile`

## Что нужно завести

1. Аккаунт `Apple Developer Program`
   - Apple указывает стоимость `99 USD / year`.
   - Источник: [Apple Developer Program](https://developer.apple.com/programs/)

2. Аккаунт `Codemagic`
   - Для individual у Codemagic есть `500 free macOS M2 minutes / month`.
   - Источник: [Codemagic pricing](https://codemagic.io/pricing/)

3. Репозиторий проекта в `GitHub`, `GitLab` или `Bitbucket`
   - Codemagic подключает репозиторий и собирает Flutter/iOS из него.
   - Источник: [Codemagic docs](https://docs.codemagic.io/getting-started/about-codemagic/)

## Что подготовить в Apple

1. Зарегистрировать `App ID` / bundle id:

```text
ru.mpb.erp.mobile
```

2. Создать приложение в `App Store Connect`
   - имя: `Enterprise Mobile`
   - bundle id: `ru.mpb.erp.mobile`

3. Создать `App Store Connect API key`
   - она нужна для интеграции Codemagic с App Store Connect

## Как подключить Codemagic

1. Подключить репозиторий.
2. Указать, что проект использует `codemagic.yaml`.
3. Создать integration с App Store Connect и назвать ее:

```text
codemagic-app-store-connect
```

Если хочешь назвать иначе, просто поменяй значение в [codemagic.yaml](c:\Users\veremyev\Desktop\crm\Новая%20папка\codemagic.yaml).

## Какие workflow уже есть

### `ios-unsigned-check`

Назначение:
- прогон `flutter analyze`
- прогон `flutter test`
- unsigned iOS build без signing

### `ios-testflight`

Назначение:
- прогон `flutter analyze`
- прогон `flutter test`
- build signed `ipa`
- отправка в `TestFlight`

## Порядок запуска

1. Сначала запусти `ios-unsigned-check`.
2. Потом настрой App Store Connect integration.
3. Затем запускай `ios-testflight`.
4. После первой успешной выгрузки открой `TestFlight` в `App Store Connect` и добавь internal testers.

Apple пишет, что `TestFlight` поддерживает до `10,000` external testers.
Источник: [Apple Developer Program](https://developer.apple.com/programs/)

## Что может потребовать ручной допил

- push notifications / APNs capabilities
- Associated Domains
- Sign in with Apple
- background modes
- camera/microphone/photo permissions
- app icons / launch assets
- privacy manifest / App Store metadata

Cloud build решает проблему отсутствия Mac для сборки, но не отменяет iOS-specific настройку проекта.
