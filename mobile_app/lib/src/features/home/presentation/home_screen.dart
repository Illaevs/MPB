import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/session_controller.dart';
import '../../activity/presentation/activity_screen.dart';
import '../../deals/presentation/deals_screen.dart';
import '../../tasks/presentation/tasks_screen.dart';
import 'overview_screen.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  int _currentIndex = 0;

  static const _pages = [
    OverviewScreen(),
    DealsScreen(),
    TasksScreen(),
    ActivityScreen(),
  ];

  static const _titles = [
    'Сводка',
    'Сделки',
    'Задачи',
    'Активность',
  ];

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(sessionControllerProvider);
    final userName = (session.user?['full_name'] as String?)?.trim();

    return Scaffold(
      appBar: AppBar(
        title: Text(_titles[_currentIndex]),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: Center(
              child: Text(
                userName == null || userName.isEmpty ? 'Пользователь' : userName,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ),
          ),
          IconButton(
            onPressed: () => ref.read(sessionControllerProvider.notifier).logout(),
            icon: const Icon(Icons.logout_rounded),
            tooltip: 'Выйти',
          ),
        ],
      ),
      body: IndexedStack(
        index: _currentIndex,
        children: _pages,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (value) => setState(() => _currentIndex = value),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.dashboard_outlined), selectedIcon: Icon(Icons.dashboard), label: 'Сводка'),
          NavigationDestination(icon: Icon(Icons.work_outline), selectedIcon: Icon(Icons.work), label: 'Сделки'),
          NavigationDestination(icon: Icon(Icons.task_outlined), selectedIcon: Icon(Icons.task), label: 'Задачи'),
          NavigationDestination(icon: Icon(Icons.timeline_outlined), selectedIcon: Icon(Icons.timeline), label: 'Лента'),
        ],
      ),
    );
  }
}
