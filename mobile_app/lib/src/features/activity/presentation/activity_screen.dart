import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/data/mobile_repository.dart';

class ActivityScreen extends ConsumerWidget {
  const ActivityScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifications = ref.watch(_notificationsProvider);
    final aiStatus = ref.watch(_aiStatusProvider);

    return RefreshIndicator(
      onRefresh: () async {
        ref.invalidate(_notificationsProvider);
        ref.invalidate(_aiStatusProvider);
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          aiStatus.when(
            data: (data) => Card(
              child: ListTile(
                leading: const Icon(Icons.smart_toy_outlined),
                title: const Text('AI ассистент'),
                subtitle: Text(
                  data['enabled'] == true
                      ? 'Подключен: ${data['model'] ?? 'неизвестная модель'}'
                      : 'Отключен',
                ),
              ),
            ),
            loading: () => const Card(
              child: ListTile(
                leading: Icon(Icons.smart_toy_outlined),
                title: Text('AI ассистент'),
                subtitle: Text('Проверка статуса...'),
              ),
            ),
            error: (error, stack) => Card(
              child: ListTile(
                leading: const Icon(Icons.smart_toy_outlined),
                title: const Text('AI ассистент'),
                subtitle: Text('Ошибка: $error'),
              ),
            ),
          ),
          const SizedBox(height: 12),
          notifications.when(
            data: (items) {
              if (items.isEmpty) {
                return const Card(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Text('Новых уведомлений нет.'),
                  ),
                );
              }
              return Column(
                children: items.map((raw) {
                  final item = (raw as Map).cast<String, dynamic>();
                  final title = (item['title'] as String?)?.trim();
                  final message = (item['message'] as String?)?.trim();
                  return Card(
                    margin: const EdgeInsets.only(bottom: 12),
                    child: ListTile(
                      title: Text(title == null || title.isEmpty ? 'Уведомление' : title),
                      subtitle: message == null || message.isEmpty ? null : Text(message),
                    ),
                  );
                }).toList(),
              );
            },
            loading: () => const Center(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: CircularProgressIndicator(),
              ),
            ),
            error: (error, stack) => Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Text('Не удалось загрузить активность:\n$error'),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

final _notificationsProvider = FutureProvider<List<dynamic>>((ref) {
  return ref.watch(mobileRepositoryProvider).loadNotifications();
});

final _aiStatusProvider = FutureProvider<Map<String, dynamic>>((ref) {
  return ref.watch(mobileRepositoryProvider).loadAiStatus();
});
