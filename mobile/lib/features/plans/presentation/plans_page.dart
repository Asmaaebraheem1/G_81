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

class PlansPage extends StatefulWidget {
  const PlansPage({super.key});

  @override
  State<PlansPage> createState() => _PlansPageState();
}

class _PlansPageState extends State<PlansPage> {
  bool _generating = false;
  late AsyncCubit<List<ReductionPlan>> _cubit;

  Future<List<ReductionPlan>> _load() =>
      context.read<CarbonRepository>().plans();

  @override
  void initState() {
    super.initState();
    _cubit = AsyncCubit<List<ReductionPlan>>(const AsyncState())..run(_load);
  }

  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  Future<void> _generate() async {
    setState(() => _generating = true);
    try {
      final locale = context.l10n.locale.languageCode;
      final plan = await context.read<CarbonRepository>().generatePlan(
            period: 'month',
            locale: locale,
          );
      if (!mounted) return;
      showSnack(context, context.tr('planGenerated'));
      await context.push('/plans/${plan.id}');
      _cubit.run(_load, silent: true);
    } catch (error) {
      if (!mounted) return;
      showSnack(context, error.toString(), error: true);
    } finally {
      if (mounted) setState(() => _generating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return Scaffold(
      appBar: AppBar(
        titleSpacing: 20,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              l10n.t('plansTitle'),
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 2),
            Text(
              l10n.t('plansSubtitle'),
              style: const TextStyle(fontSize: 11.5, color: AppColors.muted),
            ),
          ],
        ),
      ),
      body: BlocProvider.value(
        value: _cubit,
        child: RefreshIndicator(
          onRefresh: () => _cubit.run(_load, silent: true),
          child: AsyncPageBody<List<ReductionPlan>>(
            onRetry: () => _cubit.run(_load),
            builder: (plans) {
              if (plans.isEmpty) {
                return ListView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  children: [
                    const SizedBox(height: 80),
                    EmptyState(
                      message: l10n.t('noPlans'),
                      icon: Icons.route_outlined,
                      actionLabel: _generating ? null : l10n.t('generatePlan'),
                      onAction: _generating ? null : _generate,
                    ),
                  ],
                );
              }
              return ListView(
                padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
                children: [
                  FilledButton.icon(
                    onPressed: _generating ? null : _generate,
                    icon: _generating
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Icon(Icons.auto_awesome_rounded, size: 18),
                    label: Text(l10n.t('generatePlan')),
                  ),
                  const SizedBox(height: 18),
                  for (final plan in plans) ...[
                    _PlanTile(plan: plan),
                    const SizedBox(height: 11),
                  ],
                ],
              );
            },
          ),
        ),
      ),
    );
  }
}

class _PlanTile extends StatelessWidget {
  const _PlanTile({required this.plan});

  final ReductionPlan plan;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final total = plan.actions.fold<int>(
      0,
      (sum, action) => sum + action.estimatedSavingGrams,
    );
    return CarbonCard(
      onTap: () => context.push('/plans/${plan.id}'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: const BoxDecoration(
                  color: AppColors.sandSoft,
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.route_rounded, color: AppColors.forest, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      plan.title,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      '${plan.actions.length} ${l10n.t('actions')} · ${formatDate(plan.generatedAt, locale: l10n.locale.languageCode)}',
                      style: const TextStyle(fontSize: 10, color: AppColors.muted),
                    ),
                  ],
                ),
              ),
              Pill(
                label: plan.source == 'ai' ? 'AI' : l10n.t('aiRules'),
                color: plan.source == 'ai' ? AppColors.mint : AppColors.cream,
                foreground: AppColors.forest,
              ),
            ],
          ),
          const SizedBox(height: 13),
          Text(
            l10n.t('estimatedSaving'),
            style: const TextStyle(fontSize: 9.5, color: AppColors.muted),
          ),
          const SizedBox(height: 2),
          Text(
            '${formatKg(total / 1000, locale: l10n.locale.languageCode)} ${l10n.t('kgCo2e')}',
            textDirection: TextDirection.ltr,
            style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 10),
          MetricBar(
            value: plan.actions.isEmpty
                ? 0
                : plan.actions.where((a) => a.status == 'completed').length /
                    plan.actions.length,
          ),
        ],
      ),
    );
  }
}
