import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/session_controller.dart';
import '../../../core/config/app_config.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _emailController = TextEditingController(text: 'admin@nexus-demo.ru');
  final _passwordController = TextEditingController(text: 'Nexus123!');
  final _codeController = TextEditingController();
  bool _showTwoFactor = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _codeController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final controller = ref.read(sessionControllerProvider.notifier);
    final success = await controller.login(
      _emailController.text.trim(),
      _passwordController.text,
    );
    if (!mounted) return;
    if (!success && controller.pendingChallengeToken != null) {
      setState(() => _showTwoFactor = true);
    }
  }

  Future<void> _submitTwoFactor() async {
    final success = await ref.read(sessionControllerProvider.notifier).verifyTwoFactor(
          _codeController.text.trim(),
        );
    if (!mounted) return;
    if (success) {
      setState(() => _showTwoFactor = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(sessionControllerProvider);
    final theme = Theme.of(context);

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Card(
              margin: const EdgeInsets.all(24),
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      AppConfig.brandPrimary,
                      style: theme.textTheme.labelLarge?.copyWith(
                        color: const Color(0xFFDC2626),
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    Text(
                      AppConfig.brandSecondary,
                      style: theme.textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      'Enterprise система управления',
                      style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 24),
                    TextField(
                      controller: _emailController,
                      keyboardType: TextInputType.emailAddress,
                      decoration: const InputDecoration(labelText: 'Email'),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _passwordController,
                      obscureText: true,
                      decoration: const InputDecoration(labelText: 'Пароль'),
                    ),
                    if (_showTwoFactor) ...[
                      const SizedBox(height: 12),
                      TextField(
                        controller: _codeController,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(labelText: 'Код 2FA'),
                      ),
                    ],
                    if (session.error != null && session.error!.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      Text(
                        session.error!,
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.colorScheme.error,
                        ),
                      ),
                    ],
                    const SizedBox(height: 18),
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton(
                        onPressed: session.isLoading
                            ? null
                            : _showTwoFactor
                                ? _submitTwoFactor
                                : _submit,
                        child: Padding(
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          child: Text(
                            session.isLoading
                                ? 'Загрузка...'
                                : _showTwoFactor
                                    ? 'Подтвердить 2FA'
                                    : 'Войти',
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
