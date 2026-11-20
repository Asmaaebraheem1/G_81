import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/async_cubit.dart';
import '../../../core/format.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/models.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/app_widgets.dart';
import '../../dashboard/data/carbon_repository.dart';

class PlanDetailPage extends StatefulWidget {
  const PlanDetailPage({super.key, required this.planId});

  final int planId;

  @override
  State<PlanDetailPage> createState() => _PlanDetailPageState();
}

class _PlanDetailPageState extends State<PlanDetailPage> {
  late AsyncCubit<ReductionPlan> _cubit;

  Future<ReductionPlan> _load() =>
      context.read<CarbonRepository>().plan(widget.planId);

  @override
  void initState() {
    super.initState();
    _cubit = AsyncCubit<ReductionPlan>(const AsyncState())..run(_load);
  }

  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  Future<void> _setStatus(PlanAction action, String status) async {
    try {
      await context.read<CarbonRepository>().updatePlanAction(
            widget.planId,
            action.id,
            status,
          );
      if (!mounted) return;
      _cubit.run(_load, silent: true);
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
        title: Text(l10n.t('plansTitle'), style: const TextStyle(fontWeight: FontWeight.w800)),
      ),
      body: BlocProvider.value(
        value: _cubit,
        child: AsyncPageBody<ReductionPlan>(
          onRetry: () => _cubit.run(_load),
          builder: (plan) {
            final completed = plan.actions.where((a) => a.status == 'completed').length;
            final total = plan.actions.fold<int>(
              0,
              (sum, action) => sum + action.estimatedSavingGrams,
            );
            return ListView(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
              children: [
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: AppColors.forestDeep,
                    borderRadius: BorderRadius.circular(24),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        plan.title,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 19,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      const SizedBox(height: 8),
                      BidiText(
                        plan.summary,
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.66),
                          fontSize: 11.5,
                          height: 1.5,
                        ),
                      ),
                      const SizedBox(height: 18),
                      Row(
                        children: [
                          _PlanStat(
                            value: '${formatKg(total / 1000, locale: l10n.locale.languageCode)} kg',
                            label: l10n.t('estimatedSaving'),
                          ),
                          const SizedBox(width: 26),
                          _PlanStat(
                            value: '$completed/${plan.actions.length}',
                            label: l10n.t('planProgress'),
                          ),
                          const Spacer(),
                          Pill(
                            label: plan.source == 'ai' ? 'AI · free' : l10n.t('aiRules'),
                            color: Colors.white.withValues(alpha: 0.12),
                            foreground: Colors.white,
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 22),
                SectionTitle(l10n.t('actions')),
                for (final action in plan.actions) ...[
                  _ActionCard(
                    action: action,
                    onStatus: (status) => _setStatus(action, status),
                  ),
                  const SizedBox(height: 10),
                ],
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppColors.mint,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.info_outline_rounded, size: 17, color: AppColors.forest),
                      const SizedBox(width: 9),
                      Expanded(
                        child: Text(
                          l10n.isArabic
                              ? 'التوفير المقدر افتراضات موثقة في الخادم، وليس تقديرًا من الذكاء الاصطناعي.'
                              : 'Estimated savings are documented backend assumptions, not AI-generated estimates.',
                          style: const TextStyle(fontSize: 10.5, height: 1.45, color: AppColors.forest),
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

class _PlanStat extends StatelessWidget {
  const _PlanStat({required this.value, required this.label});

  final String value;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          value,
          textDirection: TextDirection.ltr,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 15,
            fontWeight: FontWeight.w800,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          label,
          style: TextStyle(
            color: Colors.white.withValues(alpha: 0.5),
            fontSize: 9,
          ),
        ),
      ],
    );
  }
}

class _ActionCard extends StatelessWidget {
  const _ActionCard({required this.action, required this.onStatus});

  final PlanAction action;
  final ValueChanged<String> onStatus;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final done = action.status == 'completed';
    final inProgress = action.status == 'in_progress';
    return CarbonCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              GestureDetector(
                onTap: () => onStatus(done ? 'pending' : 'completed'),
                child: Container(
                  width: 24,
                  height: 24,
                  margin: const EdgeInsets.only(top: 1),
                  decoration: BoxDecoration(
                    color: done ? AppColors.forest : Colors.transparent,
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: done ? AppColors.forest : AppColors.line,
                      width: 1.6,
                    ),
                  ),
                  child: done
                      ? const Icon(Icons.check_rounded, size: 15, color: Colors.white)
                      : null,
                ),
              ),
              const SizedBox(width: 11),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    BidiText(
                      action.title,
                      style: TextStyle(
                        fontSize: 12.5,
                        fontWeight: FontWeight.w700,
                        decoration: done ? TextDecoration.lineThrough : null,
                        color: done ? AppColors.muted : AppColors.ink,
                      ),
                    ),
                    const SizedBox(height: 4),
                    BidiText(
                      action.description,
                      style: const TextStyle(fontSize: 10.5, height: 1.45, color: AppColors.muted),
                    ),
                  ],
                ),
              ),
              PopupMenuButton<String>(
                padding: EdgeInsets.zero,
                icon: const Icon(Icons.more_vert_rounded, size: 18),
                onSelected: onStatus,
                itemBuilder: (context) => [
                  PopupMenuItem(value: 'pending', child: Text(l10n.t('pending'))),
                  PopupMenuItem(value: 'in_progress', child: Text(l10n.t('inProgress'))),
                  PopupMenuItem(value: 'completed', child: Text(l10n.t('completed'))),
                  PopupMenuItem(value: 'skipped', child: Text(l10n.t('skipped'))),
                ],
              ),
            ],
          ),
          const SizedBox(height: 11),
          Row(
            children: [
              Pill(
                label: l10n.t(done ? 'completed' : (inProgress ? 'inProgress' : action.status)),
                color: done
                    ? AppColors.mint
                    : inProgress
                        ? AppColors.sandSoft
                        : AppColors.cream,
                foreground: done
                    ? AppColors.forest
                    : inProgress
                        ? const Color(0xFF8C5A2B)
                        : AppColors.muted,
              ),
              const SizedBox(width: 7),
              Pill(label: l10n.t(action.priority), color: AppColors.cream, foreground: AppColors.muted),
              const Spacer(),
              if (action.estimatedSavingGrams > 0)
                Text(
                  '−${formatKg(action.estimatedSavingGrams / 1000, locale: l10n.locale.languageCode)} kg',
                  textDirection: TextDirection.ltr,
                  style: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w800),
                ),
            ],
          ),
          if (action.savingAssumption.isNotEmpty) ...[
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppColors.cream,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.calculate_outlined, size: 14, color: AppColors.muted),
                  const SizedBox(width: 7),
                  Expanded(
                    child: BidiText(
                      action.savingAssumption,
                      style: const TextStyle(fontSize: 9.5, height: 1.4, color: AppColors.muted),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}
