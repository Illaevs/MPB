import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:enterprise_mobile/src/features/auth/presentation/login_screen.dart';

void main() {
  testWidgets('Login screen renders', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(
          home: LoginScreen(),
        ),
      ),
    );

    expect(find.text('Enterprise система управления'), findsOneWidget);
    expect(find.text('Email'), findsOneWidget);
    expect(find.text('Пароль'), findsOneWidget);
  });
}
