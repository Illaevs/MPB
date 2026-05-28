import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/data/mobile_repository.dart';

class DealsScreen extends ConsumerWidget {
  const DealsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final future = ref.watch(_dealsProvider);
    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(_dealsProvider),
      child: future.when(
        data: (items) {
          if (items.isEmpty) {
            return ListView(
              padding: const EdgeInsets.all(16),
              children: const [
                Card(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Text('Сделок пока нет.'),
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
              final objectName = (item['obj_name'] as String?)?.trim();
              final address = (item['address'] as String?)?.trim();
              final status = (item['status'] as String?)?.trim();
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title == null || title.isEmpty ? 'Без названия' : title,
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
                      ),
                      if (objectName != null && objectName.isNotEmpty) ...[
                        const SizedBox(height: 6),
                        Text(objectName),
                      ],
                      if (address != null && address.isNotEmpty) ...[
                        const SizedBox(height: 4),
                        Text(
                          address,
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                      if (status != null && status.isNotEmpty) ...[
                        const SizedBox(height: 10),
                        Chip(label: Text(status)),
                      ],
                    ],
                  ),
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
                child: Text('Не удалось загрузить сделки:\n$error'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

final _dealsProvider = FutureProvider<List<dynamic>>((ref) {
  return ref.watch(mobileRepositoryProvider).loadDeals();
});
