import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/data/mobile_repository.dart';

class OverviewScreen extends ConsumerWidget {
  const OverviewScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final future = ref.watch(_overviewProvider);
    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(_overviewProvider),
      child: future.when(
        data: (data) {
          final cards = [
            _MetricCard('Активные сделки', '${data['active_deals'] ?? 0}', Icons.work),
            _MetricCard('Просроченные задачи', '${data['overdue_tasks'] ?? 0}', Icons.warning_amber_rounded),
            _MetricCard('Новые документы 7д', '${data['new_documents_7d'] ?? 0}', Icons.description_outlined),
            _MetricCard('Непрочитанные', '${data['unread_notifications'] ?? 0}', Icons.notifications_outlined),
          ];
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              ...cards,
              const SizedBox(height: 8),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Mobile MVP scope',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
                      ),
                      const SizedBox(height: 8),
                      const Text('Сейчас мобильный слой стартует как компактная роль-ориентированная проекция: сводка, сделки, задачи, активность.'),
                    ],
                  ),
                ),
              ),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Text('Не удалось загрузить сводку:\n$error'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

final _overviewProvider = FutureProvider<Map<String, dynamic>>((ref) {
  return ref.watch(mobileRepositoryProvider).loadDashboardSummary();
});

class _MetricCard extends StatelessWidget {
  const _MetricCard(this.title, this.value, this.icon);

  final String title;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            CircleAvatar(
              radius: 24,
              child: Icon(icon),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: Theme.of(context).textTheme.bodyMedium),
                  const SizedBox(height: 2),
                  Text(
                    value,
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
