import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../core/async_cubit.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/models.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/app_widgets.dart';
import '../../auth/presentation/auth_cubit.dart';
import '../../dashboard/data/carbon_repository.dart';
import 'settings_cubit.dart';

typedef SettingsData = ({
  Map<String, dynamic> profile,
  Map<String, dynamic>? ai,
});

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  late AsyncCubit<SettingsData> _cubit;

  Future<SettingsData> _load() async {
    final repo = context.read<CarbonRepository>();
    final profile = await repo.profile();
    Map<String, dynamic>? ai;
    try {
      ai = await repo.aiStatus();
    } catch (_) {
      ai = null;
    }
    return (profile: profile, ai: ai);
  }

  @override
  void initState() {
    super.initState();
    _cubit = AsyncCubit<SettingsData>(const AsyncState())..run(_load);
  }

  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  Future<void> _signOut() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(context.tr('signOut')),
        content: Text(context.tr('logoutConfirm')),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(context.tr('cancel')),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(context.tr('signOut')),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    await context.read<AuthCubit>().logout();
    if (mounted) context.go('/');
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final user = context.watch<AuthCubit>().state.user;
    final settings = context.watch<SettingsCubit>().state;
    return Scaffold(
      appBar: AppBar(
        title: Text(
          l10n.t('settingsTitle'),
          style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
        ),
      ),
      body: BlocProvider.value(
        value: _cubit,
        child: BlocListener<SettingsCubit, SettingsState>(
          listener: (context, state) => setState(() {}),
          child: AsyncPageBody<SettingsData>(
            onRetry: () => _cubit.run(_load),
            builder: (data) => ListView(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
              children: [
                _AccountCard(user: user),
                const SizedBox(height: 22),
                SectionTitle(l10n.t('language')),
                CarbonCard(
                  child: Row(
                    children: [
                      const Icon(Icons.translate_rounded, size: 20, color: AppColors.forest),
                      const SizedBox(width: 11),
                      Expanded(
                        child: Text(
                          l10n.t('appLanguage'),
                          style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600),
                        ),
                      ),
                      SegmentedButton<String>(
                        segments: [
                          ButtonSegment(value: 'en', label: Text(l10n.t('english'))),
                          ButtonSegment(value: 'ar', label: Text(l10n.t('arabic'))),
                        ],
                        selected: {settings.locale.languageCode},
                        showSelectedIcon: false,
                        style: ButtonStyle(
                          visualDensity: VisualDensity.compact,
                          textStyle: WidgetStateProperty.all(
                            const TextStyle(fontSize: 10, fontWeight: FontWeight.w700),
                          ),
                        ),
                        onSelectionChanged: (value) =>
                            context.read<SettingsCubit>().setLanguage(value.first),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 22),
                SectionTitle(l10n.t('profile')),
                _ProfileEditor(
                  profile: data.profile,
                  onSaved: () {
                    context.read<AuthCubit>().refreshUser();
                    _cubit.run(_load, silent: true);
                  },
                ),
                const SizedBox(height: 22),
                SectionTitle(l10n.t('aiStatus')),
                _AiCard(ai: data.ai),
                const SizedBox(height: 22),
                SectionTitle(l10n.t('account')),
                CarbonCard(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Column(
                    children: [
                      ListTile(
                        leading: const Icon(Icons.lock_outline_rounded, size: 21),
                        title: Text(
                          l10n.t('changePassword'),
                          style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600),
                        ),
                        trailing: const Icon(Icons.chevron_right_rounded, size: 19),
                        onTap: () => _showPasswordDialog(context),
                      ),
                      if (user?.organizationId != null)
                        ListTile(
                          leading: const Icon(Icons.business_rounded, size: 21),
                          title: Text(
                            l10n.t('organizationProfile'),
                            style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600),
                          ),
                          trailing: const Icon(Icons.chevron_right_rounded, size: 19),
                          onTap: () => context.push('/organization'),
                        ),
                      ListTile(
                        leading: const Icon(Icons.info_outline_rounded, size: 21),
                        title: Text(
                          l10n.t('about'),
                          style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600),
                        ),
                        trailing: const Text(
                          'v1.0.0',
                          style: TextStyle(fontSize: 10, color: AppColors.muted),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                OutlinedButton.icon(
                  onPressed: _signOut,
                  icon: const Icon(Icons.logout_rounded, size: 18),
                  label: Text(l10n.t('signOut')),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppColors.danger,
                    side: const BorderSide(color: AppColors.danger),
                  ),
                ),
                const SizedBox(height: 18),
                Text(
                  l10n.t('demoMode'),
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 9.5, color: AppColors.muted),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _showPasswordDialog(BuildContext context) async {
    final current = TextEditingController();
    final next = TextEditingController();
    final formKey = GlobalKey<FormState>();
    final saved = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(context.tr('changePassword')),
        content: Form(
          key: formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextFormField(
                controller: current,
                obscureText: true,
                decoration: InputDecoration(labelText: context.tr('currentPassword')),
                validator: (value) => (value ?? '').length < 8
                    ? context.tr('validationError')
                    : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: next,
                obscureText: true,
                decoration: InputDecoration(labelText: context.tr('newPassword')),
                validator: (value) => (value ?? '').length < 8
                    ? context.tr('validationError')
                    : null,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: Text(context.tr('cancel')),
          ),
          FilledButton(
            onPressed: () {
              if (formKey.currentState?.validate() ?? false) {
                Navigator.pop(dialogContext, true);
              }
            },
            child: Text(context.tr('save')),
          ),
        ],
      ),
    );
    if (saved != true || !mounted) return;
    try {
      await context.read<CarbonRepository>().changePassword(
            currentPassword: current.text,
            newPassword: next.text,
          );
      if (!mounted) return;
      showSnack(context, context.tr('passwordChanged'));
    } catch (error) {
      if (!mounted) return;
      showSnack(context, error.toString(), error: true);
    }
  }
}

class _AccountCard extends StatelessWidget {
  const _AccountCard({required this.user});

  final SessionUser? user;

  @override
  Widget build(BuildContext context) {
    final name = user?.fullName ?? '—';
    return CarbonCard(
      color: AppColors.forestDeep,
      child: Row(
        children: [
          Container(
            width: 54,
            height: 54,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.12),
              shape: BoxShape.circle,
            ),
            child: Center(
              child: Text(
                name.isEmpty ? '?' : name.substring(0, 1).toUpperCase(),
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  user?.email ?? '',
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.55),
                    fontSize: 10.5,
                  ),
                ),
              ],
            ),
          ),
          if (user?.isOrganization == true)
            Pill(
              label: context.tr('organization'),
              color: Colors.white.withValues(alpha: 0.12),
              foreground: Colors.white,
            ),
        ],
      ),
    );
  }
}

class _ProfileEditor extends StatefulWidget {
  const _ProfileEditor({required this.profile, required this.onSaved});

  final Map<String, dynamic> profile;
  final VoidCallback onSaved;

  @override
  State<_ProfileEditor> createState() => _ProfileEditorState();
}

class _ProfileEditorState extends State<_ProfileEditor> {
  late final TextEditingController _name;
  late final TextEditingController _alias;
  late int _household;
  late bool _optIn;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    final user = context.read<AuthCubit>().state.user;
    _name = TextEditingController(text: user?.fullName ?? '');
    _alias = TextEditingController(text: s(widget.profile['leaderboard_alias']));
    _household = ni(widget.profile['household_size'], 1).clamp(1, 20);
    _optIn = widget.profile['leaderboard_opt_in'] == true;
  }

  @override
  void dispose() {
    _name.dispose();
    _alias.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      final repo = context.read<CarbonRepository>();
      final locale = context.l10n.locale.languageCode;
      await repo.updateMe({'full_name': _name.text.trim(), 'locale': locale});
      await repo.updateProfile({
        'household_size': _household,
        'leaderboard_opt_in': _optIn,
        if (_alias.text.trim().isNotEmpty) 'leaderboard_alias': _alias.text.trim(),
      });
      if (!mounted) return;
      showSnack(context, context.tr('saved'));
      widget.onSaved();
    } catch (error) {
      if (!mounted) return;
      showSnack(context, error.toString(), error: true);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return CarbonCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(l10n.t('fullName'), style: _labelStyle),
          const SizedBox(height: 7),
          TextFormField(
            controller: _name,
            decoration: const InputDecoration(prefixIcon: Icon(Icons.person_outline_rounded)),
          ),
          const SizedBox(height: 15),
          Text(l10n.t('householdSize'), style: _labelStyle),
          const SizedBox(height: 7),
          DropdownButtonFormField<int>(
            initialValue: _household,
            decoration: const InputDecoration(prefixIcon: Icon(Icons.groups_outlined)),
            items: [
              for (var i = 1; i <= 10; i++)
                DropdownMenuItem(value: i, child: Text('$i')),
            ],
            onChanged: (value) => setState(() => _household = value ?? 1),
          ),
          const SizedBox(height: 12),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            activeThumbColor: AppColors.forest,
            title: Text(
              l10n.t('optIn'),
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
            ),
            subtitle: Text(
              l10n.isArabic
                  ? 'يظهر الاسم المستعار فقط، وليس بريدك الإلكتروني.'
                  : 'Only your alias appears, never your email.',
              style: const TextStyle(fontSize: 9, color: AppColors.muted),
            ),
            value: _optIn,
            onChanged: (value) => setState(() => _optIn = value),
          ),
          if (_optIn) ...[
            const SizedBox(height: 4),
            TextFormField(
              controller: _alias,
              textDirection: TextDirection.ltr,
              textAlign: TextAlign.right,
              decoration: InputDecoration(
                labelText: l10n.t('leaderboard'),
                prefixIcon: const Icon(Icons.badge_outlined),
              ),
            ),
          ],
          const SizedBox(height: 16),
          FilledButton(
            onPressed: _saving ? null : _save,
            child: _saving
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : Text(l10n.t('saveChanges')),
          ),
        ],
      ),
    );
  }

  TextStyle get _labelStyle => const TextStyle(
        fontSize: 11,
        fontWeight: FontWeight.w700,
        color: AppColors.ink,
      );
}

class _AiCard extends StatelessWidget {
  const _AiCard({required this.ai});

  final Map<String, dynamic>? ai;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final enabled = ai?['enabled'] == true;
    final budget = map(ai?['budget']);
    return CarbonCard(
      child: Column(
        children: [
          Row(
            children: [
              Container(
                width: 38,
                height: 38,
                decoration: const BoxDecoration(
                  color: AppColors.mint,
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.auto_awesome_rounded, color: AppColors.forest, size: 18),
              ),
              const SizedBox(width: 11),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      enabled ? l10n.t('aiEnabled') : l10n.t('aiDisabled'),
                      style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      '${l10n.t('model')}: ${s(ai?['model'], 'openrouter/free')}',
                      style: const TextStyle(fontSize: 9.5, color: AppColors.muted),
                    ),
                  ],
                ),
              ),
              Pill(
                label: enabled ? l10n.t('on') : l10n.t('off'),
                color: enabled ? AppColors.mint : AppColors.cream,
                foreground: enabled ? AppColors.forest : AppColors.muted,
              ),
            ],
          ),
          if (budget.isNotEmpty) ...[
            const Divider(height: 24),
            Row(
              children: [
                Expanded(
                  child: Text(
                    '${l10n.t('aiStatus')} · ${ni(budget['remaining'])} / ${ni(budget['daily_token_limit'])}',
                    style: const TextStyle(fontSize: 9.5, color: AppColors.muted),
                  ),
                ),
                Text(
                  '${ni(budget['used_today'])}',
                  style: const TextStyle(fontSize: 9.5, fontWeight: FontWeight.w700),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
