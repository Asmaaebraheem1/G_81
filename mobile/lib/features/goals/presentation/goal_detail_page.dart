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

class GoalDetailPage extends StatefulWidget {
  const GoalDetailPage({super.key, required this.goalId});

  final int goalId;

  @override
  State<GoalDetailPage> createState() => _GoalDetailPageState();
}

class _GoalDetailPageState extends State<GoalDetailPage> {
  late AsyncCubit<Goal> _cubit;

  Future<Goal> _load() => context.read<CarbonRepository>().goal(widget.goalId);

  @override
  void initState() {
    super.initState();
    _cubit = AsyncCubit<Goal>(const AsyncState())..run(_load);
  }

  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  Future<void> _cancel() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(context.tr('cancelGoal')),
        content: Text(context.tr('cancelGoal')),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(context.tr('cancel')),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(context.tr('confirm')),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    try {
      await context.read<CarbonRepository>().cancelGoal(widget.goalId);
      if (!mounted) return;
      showSnack(context, context.tr('saved'));
      context.pop(true);
    } catch (error) {
      if (!mounted) return;
      showSnack(context, error.toString(), error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.t('goalProgress'), style: const TextStyle(fontWeight: FontWeight.w800)),
        actions: [
          IconButton(
            onPressed: _cancel,
            icon: const Icon(Icons.cancel_outlined),
          ),
        ],
      ),
      body: BlocProvider.value(
        value: _cubit,
        child: AsyncPageBody<Goal>(
          onRetry: () => _cubit.run(_load),
          builder: (goal) => _GoalDetail(goal: goal),
        ),
      ),
    );
  }
}

class _GoalDetail extends StatelessWidget {
  const _GoalDetail({required this.goal});

  final Goal goal;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final locale = l10n.locale.languageCode;
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
      children: [
        Container(
          padding: const EdgeInsets.all(22),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [AppColors.forestDeep, AppColors.forest],
            ),
            borderRadius: BorderRadius.circular(26),
          ),
          child: Column(
            children: [
              Text(
                goal.title,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 18),
              SizedBox(
                width: 142,
                height: 142,
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    SizedBox(
                      width: 142,
                      height: 142,
                      child: CircularProgressIndicator(
                        value: goal.achievedPercent / 100,
                        strokeWidth: 12,
                        strokeCap: StrokeCap.round,
                        backgroundColor: Colors.white.withValues(alpha: 0.1),
                        valueColor: const AlwaysStoppedAnimation(AppColors.sand),
                      ),
                    ),
                    Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          '${goal.achievedPercent.round()}%',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 30,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        Text(
                          l10n.t('achieved'),
                          style: TextStyle(
                            color: Colors.white.withValues(alpha: 0.55),
                            fontSize: 10,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 18),
              Text(
                '${formatKg(goal.currentKg, locale: locale)} / ${formatKg(goal.targetKg, locale: locale)} ${l10n.t('kg')}',
                textDirection: TextDirection.ltr,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 15,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                '${goal.daysLeft} ${l10n.t('daysLeft')}',
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.55),
                  fontSize: 10,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),
        CarbonCard(
          child: Column(
            children: [
              DetailRow(label: l10n.t('targetPercent'), value: '${goal.targetPercent.round()}%'),
              DetailRow(label: l10n.t('baseline'), value: '${formatKg(goal.baselineKg, locale: locale)} ${l10n.t('kg')}', ltr: true),
              DetailRow(label: l10n.t('current'), value: '${formatKg(goal.currentKg, locale: locale)} ${l10n.t('kg')}', ltr: true),
              DetailRow(label: l10n.t('endDate'), value: formatDate(goal.endDate, locale: locale)),
              DetailRow(
                label: l10n.t('onTrack'),
                value: goal.onTrack ? '✓' : '—',
                valueColor: goal.onTrack ? AppColors.forest : AppColors.danger,
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: AppColors.mint,
            borderRadius: BorderRadius.circular(16),
          ),
          child: Row(
            children: [
              const Icon(Icons.lock_outline_rounded, size: 17, color: AppColors.forest),
              const SizedBox(width: 9),
              Expanded(
                child: Text(
                  l10n.isArabic
                      ? 'خط الأساس محفوظ من سجلاتك، ويُعاد حساب التقدم من الخادم فقط.'
                      : 'The baseline is snapshotted from your records; progress is recalculated by the backend only.',
                  style: const TextStyle(fontSize: 10.5, height: 1.4, color: AppColors.forest),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
