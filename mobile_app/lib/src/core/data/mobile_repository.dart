import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../network/api_client.dart';

final mobileRepositoryProvider = Provider<MobileRepository>((ref) {
  return MobileRepository(ref.watch(apiClientProvider));
});

class MobileRepository {
  MobileRepository(this._client);

  final ApiClient _client;

  Future<Map<String, dynamic>> loadDashboardSummary() {
    return _client.getJson('/api/v1/dashboard/summary');
  }

  Future<List<dynamic>> loadDeals() {
    return _client.getList('/api/v1/deals', queryParameters: {'limit': 25});
  }

  Future<List<dynamic>> loadTasks() {
    return _client.getList('/api/v1/tasks', queryParameters: {'limit': 25});
  }

  Future<Map<String, dynamic>> loadDealActivity(String dealId) {
    return _client.getJson('/api/v1/deals/$dealId/activity', queryParameters: {'limit': 20});
  }

  Future<List<dynamic>> loadNotifications() {
    return _client.getList('/api/v1/notifications', queryParameters: {'limit': 20});
  }

  Future<Map<String, dynamic>> loadAiStatus() {
    return _client.getJson('/api/v1/ai/status');
  }
}

