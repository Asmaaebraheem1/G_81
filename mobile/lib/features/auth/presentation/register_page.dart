import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/app_localizations.dart';
import '../../../core/theme/app_theme.dart';
import 'auth_cubit.dart';

class RegisterPage extends StatefulWidget {
  const RegisterPage({super.key});

  @override
  State<RegisterPage> createState() => _RegisterPageState();
}

class _RegisterPageState extends State<RegisterPage> {
  final _formKey = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _confirm = TextEditingController();
  final _orgName = TextEditingController();
  String _accountType = 'individual';
  bool _obscure = true;

  @override
  void dispose() {
    _name.dispose();
    _email.dispose();
    _password.dispose();
    _confirm.dispose();
    _orgName.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    final locale = Localizations.localeOf(context).languageCode;
    final ok = await context.read<AuthCubit>().register(
          fullName: _name.text,
          email: _email.text,
          password: _password.text,
          accountType: _accountType,
          locale: locale,
          organizationName: _accountType == 'organization' ? _orgName.text : null,
        );
    if (ok && mounted) context.go('/home');
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return Scaffold(
      body: SafeArea(
        child: BlocConsumer<AuthCubit, AuthState>(
          listenWhen: (previous, current) => current.error != null && previous.error != current.error,
          listener: (context, state) {
            if (state.error != null) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text(state.error!), backgroundColor: AppColors.danger),
              );
            }
          },
          builder: (context, state) {
            return SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(24, 8, 24, 30),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Align(
                      alignment: AlignmentDirectional.centerStart,
                      child: IconButton(
                        onPressed: () => context.go('/'),
                        icon: const Icon(Icons.arrow_back_rounded),
                      ),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      l10n.t('createAccountTitle'),
                      style: const TextStyle(
                        fontSize: 30,
                        fontWeight: FontWeight.w800,
                        letterSpacing: -0.8,
                        height: 1.15,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      l10n.t('createAccountSubtitle'),
                      style: const TextStyle(color: AppColors.muted),
                    ),
                    const SizedBox(height: 26),
                    Text(l10n.t('fullName'), style: _labelStyle),
                    const SizedBox(height: 7),
                    TextFormField(
                      controller: _name,
                      textInputAction: TextInputAction.next,
                      decoration: const InputDecoration(
                        prefixIcon: Icon(Icons.person_outline_rounded, size: 20),
                        hintText: 'Sara Ahmed',
                      ),
                      validator: (value) => (value ?? '').trim().length < 2
                          ? l10n.t('validationError')
                          : null,
                    ),
                    const SizedBox(height: 16),
                    Text(l10n.t('email'), style: _labelStyle),
                    const SizedBox(height: 7),
                    TextFormField(
                      controller: _email,
                      keyboardType: TextInputType.emailAddress,
                      textInputAction: TextInputAction.next,
                      decoration: const InputDecoration(
                        prefixIcon: Icon(Icons.alternate_email_rounded, size: 20),
                        hintText: 'you@example.com',
                      ),
                      validator: (value) => !(value ?? '').contains('@')
                          ? l10n.t('validationError')
                          : null,
                    ),
                    const SizedBox(height: 16),
                    Text(l10n.t('accountType'), style: _labelStyle),
                    const SizedBox(height: 8),
                    SegmentedButton<String>(
                      segments: [
                        ButtonSegment(value: 'individual', label: Text(l10n.t('individual'))),
                        ButtonSegment(value: 'household', label: Text(l10n.t('household'))),
                        ButtonSegment(value: 'organization', label: Text(l10n.t('organizationType'))),
                      ],
                      selected: {_accountType},
                      onSelectionChanged: (value) => setState(() => _accountType = value.first),
                      showSelectedIcon: false,
                      style: ButtonStyle(
                        visualDensity: VisualDensity.compact,
                        textStyle: WidgetStateProperty.all(
                          const TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
                        ),
                      ),
                    ),
                    if (_accountType == 'organization') ...[
                      const SizedBox(height: 16),
                      Text(l10n.t('organizationName'), style: _labelStyle),
                      const SizedBox(height: 7),
                      TextFormField(
                        controller: _orgName,
                        textInputAction: TextInputAction.next,
                        decoration: const InputDecoration(
                          prefixIcon: Icon(Icons.business_rounded, size: 20),
                        ),
                        validator: (value) => _accountType == 'organization' &&
                                (value ?? '').trim().length < 2
                            ? l10n.t('validationError')
                            : null,
                      ),
                    ],
                    const SizedBox(height: 16),
                    Text(l10n.t('password'), style: _labelStyle),
                    const SizedBox(height: 7),
                    TextFormField(
                      controller: _password,
                      obscureText: _obscure,
                      textInputAction: TextInputAction.next,
                      decoration: InputDecoration(
                        prefixIcon: const Icon(Icons.lock_outline_rounded, size: 20),
                        suffixIcon: IconButton(
                          onPressed: () => setState(() => _obscure = !_obscure),
                          icon: Icon(
                            _obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined,
                            size: 20,
                          ),
                        ),
                      ),
                      validator: (value) => (value ?? '').length < 8
                          ? l10n.t('validationError')
                          : null,
                    ),
                    const SizedBox(height: 16),
                    Text(l10n.t('confirmPassword'), style: _labelStyle),
                    const SizedBox(height: 7),
                    TextFormField(
                      controller: _confirm,
                      obscureText: _obscure,
                      textInputAction: TextInputAction.done,
                      onFieldSubmitted: (_) => _submit(),
                      decoration: const InputDecoration(
                        prefixIcon: Icon(Icons.lock_outline_rounded, size: 20),
                      ),
                      validator: (value) => value != _password.text
                          ? l10n.t('validationError')
                          : null,
                    ),
                    const SizedBox(height: 24),
                    FilledButton(
                      onPressed: state.submitting ? null : _submit,
                      child: state.submitting
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : Text(l10n.t('createAccount')),
                    ),
                    const SizedBox(height: 12),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          l10n.t('haveAccount'),
                          style: const TextStyle(color: AppColors.muted, fontSize: 13),
                        ),
                        TextButton(
                          onPressed: () => context.go('/login'),
                          child: Text(l10n.t('signIn')),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  TextStyle get _labelStyle => const TextStyle(
        fontSize: 12,
        fontWeight: FontWeight.w700,
        color: AppColors.ink,
      );
}
