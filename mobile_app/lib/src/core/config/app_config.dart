class AppConfig {
  const AppConfig._();

  static const String appName = 'Enterprise система управления';
  static const String brandPrimary = 'МПБ № 1';
  static const String brandSecondary = 'tech';
  static const String defaultBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://mpb-erp.ru',
  );
}

