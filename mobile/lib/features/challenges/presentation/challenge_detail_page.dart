import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../core/async_cubit.dart';
import '../../../core/format.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/models.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/app_widgets.dart';
import '../../dashboard/data/carbon_repository.dart';

class ChallengeDetailPage extends StatefulWidget {
  const ChallengeDetailPage({super.key, required this.challengeId});

  final int challengeId;

  @override
  State<ChallengeDetailPage> createState() => _ChallengeDetailPageState();
}

class _ChallengeDetailPageState extends State<ChallengeDetailPage> {
  late AsyncCubit<Map<String, dynamic>> _cubit;
  bool _busy = false;

  Future<Map<String, dynamic>> _load() =>
      context.read<CarbonRepository>().challengeDetail(widget.challengeId);

  @override
  void initState() {
    super.initState();
    _cubit = AsyncCubit<Map<String, dynamic>>(const AsyncState())..run(_load);
  }

  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  Future<void> _join() async {
    setState(() => _busy = true);
    try {
      await context.read<CarbonRepository>().joinChallenge(widget.challengeId);
      if (!mounted) return;
      _cubit.run(_load, silent: true);
    } catch (error) {
      if (!mounted) return;
      showSnack(context, error.toString(), error: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _logProgress(bool verified) async {
    double? value;
    if (!verified) {
      final controller = TextEditingController();
      value = await showDialog<double>(
        context: context,
        builder: (context) => AlertDialog(
          title: Text(context.tr('selfReport')),
          content: TextField(
            controller: controller,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            autofocus: true,
            decoration: const InputDecoration(hintText: '0'),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text(context.tr('cancel')),
            ),
            FilledButton(
              onPressed: () =>
                  Navigator.pop(context, double.tryParse(controller.text.trim())),
              child: Text(context.tr('save')),
            ),
          ],
        ),
      );
      if (value == null) return;
    }
    setState(() => _busy = true);
    try {
      await context.read<CarbonRepository>().reportChallengeProgress(
            widget.challengeId,
            value: value,
          );
      if (!mounted) return;
      _cubit.run(_load, silent: true);
    } catch (error) {
      if (!mounted) return;
      showSnack(context, error.toString(), error: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return Scaffold(
      appBar: AppBar(
        title: Text(
          l10n.t('challengesTitle'),
          style: const TextStyle(fontWeight: FontWeight.w800),
        ),
        actions: [
          IconButton(
            onPressed: () => context.push('/leaderboard'),
            icon: const Icon(Icons.leaderboard_outlined),
          ),
        ],
      ),
      body: BlocProvider.value(
        value: _cubit,
        child: AsyncPageBody<Map<String, dynamic>>(
          onRetry: () => _cubit.run(_load),
          builder: (data) {
            final challenge = Challenge.fromJson(data);
            final progress = map(data['progress']);
            final participation = map(data['participation']);
            final joined = participation.isNotEmpty;
            final value = n(progress['value']);
            final target = n(progress['target_value']);
            final percent = n(progress['percent']);
            final completed = s(participation['status']) == 'completed';
            final verified = progress['verified'] == true;
            return ListView(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
              children: [
                Container(
                  padding: const EdgeInsets.all(22),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [Color(0xFF6A4B1F), Color(0xFF9A6E31)],
                    ),
                    borderRadius: BorderRadius.circular(26),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.emoji_events_rounded, color: AppColors.sandSoft, size: 22),
                          const Spacer(),
                          Pill(
                            label: '${challenge.points} ${l10n.t('points')}',
                            color: Colors.white.withValues(alpha: 0.14),
                            foreground: Colors.white,
                          ),
                        ],
                      ),
                      const SizedBox(height: 14),
                      Text(
                        challenge.title(l10n.locale.languageCode),
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 22,
                          fontWeight: FontWeight.w800,
                          height: 1.2,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        challenge.description(l10n.locale.languageCode),
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.7),
                          fontSize: 11.5,
                          height: 1.5,
                        ),
                      ),
                      const SizedBox(height: 20),
                      Row(
                        children: [
                          Text(
                            '${value.round()} / ${target.round()}',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 18,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                          const Spacer(),
                          Text(
                            formatPercent(percent),
                            style: const TextStyle(
                              color: AppColors.sandSoft,
                              fontSize: 16,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      MetricBar(
                        value: percent / 100,
                        color: AppColors.sand,
                        background: Colors.white.withValues(alpha: 0.15),
                        height: 9,
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                CarbonCard(
                  child: Column(
                    children: [
                      DetailRow(
                        label: l10n.t('progress'),
                        value: '${value.round()} / ${target.round()}',
                      ),
                      DetailRow(
                        label: l10n.t('completion'),
                        value: formatPercent(percent),
                      ),
                      DetailRow(
                        label: l10n.t('startDate'),
                        value: formatDate(challenge.startDate, locale: l10n.locale.languageCode),
                      ),
                      DetailRow(
                        label: l10n.t('endDate'),
                        value: formatDate(challenge.endDate, locale: l10n.locale.languageCode),
                      ),
                      DetailRow(
                        label: l10n.t('source'),
                        value: verified ? l10n.t('verified') : l10n.t('selfReported'),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 22),
                if (!joined)
                  FilledButton(
                    onPressed: _busy ? null : _join,
                    child: _busy
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : Text(l10n.t('join')),
                  )
                else if (completed)
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppColors.mint,
                      borderRadius: BorderRadius.circular(18),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.verified_rounded, color: AppColors.forest),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            l10n.t('challengeCompleted'),
                            style: const TextStyle(
                              fontWeight: FontWeight.w700,
                              color: AppColors.forest,
                            ),
                          ),
                        ),
                      ],
                    ),
                  )
                else
                  OutlinedButton.icon(
                    onPressed: _busy ? null : () => _logProgress(verified),
                    icon: const Icon(Icons.add_task_rounded, size: 18),
                    label: Text(l10n.t('selfReport')),
                  ),
                const SizedBox(height: 14),
                Container(
                  padding: const EdgeInsets.all(13),
                  decoration: BoxDecoration(
                    color: AppColors.cream,
                    borderRadius: BorderRadius.circular(15),
                    border: Border.all(color: AppColors.line),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.shield_outlined, size: 17, color: AppColors.muted),
                      const SizedBox(width: 9),
                      Expanded(
                        child: Text(
                          l10n.isArabic
                              ? 'يُحسب التقدم من سجلاتك في الخادم متى أمكن، وإلا يُسجّل ذاتيًا.'
                              : 'Progress is calculated from your backend records where possible, otherwise self-reported.',
                          style: const TextStyle(fontSize: 9.5, height: 1.4, color: AppColors.muted),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}
