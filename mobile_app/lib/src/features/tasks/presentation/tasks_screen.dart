import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/data/mobile_repository.dart';

class TasksScreen extends ConsumerWidget {
  const TasksScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final future = ref.watch(_tasksProvider);
    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(_tasksProvider),
      child: future.when(
        data: (items) {
          if (items.isEmpty) {
            return ListView(
              padding: const EdgeInsets.all(16),
              children: const [
                Card(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Text('Задач пока нет.'),
                  ),
                ),
              ],
            );
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: items.length,
            separatorBuilder: (context, index) => const SizedBox(height: 12),
            itemBuilder: (context, index) {
              final item = (items[index] as Map).cast<String, dynamic>();
              final title = (item['title'] as String?)?.trim();
              final status = (item['status'] as String?)?.trim();
              final dueDate = (item['due_date'] as String?)?.trim();
              final dealTitle = (item['deal_title'] as String?)?.trim();

              return Card(
                child: ListTile(
                  title: Text(title == null || title.isEmpty ? 'Без названия' : title),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (dealTitle != null && dealTitle.isNotEmpty) Text(dealTitle),
                      if (dueDate != null && dueDate.isNotEmpty) Text('Срок: $dueDate'),
                    ],
                  ),
                  trailing: status == null || status.isEmpty ? null : Chip(label: Text(status)),
                ),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Text('Не удалось загрузить задачи:\n$error'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

final _tasksProvider = FutureProvider<List<dynamic>>((ref) {
  return ref.watch(mobileRepositoryProvider).loadTasks();
});
