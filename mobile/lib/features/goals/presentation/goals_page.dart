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

class GoalsPage extends StatefulWidget {
  const GoalsPage({super.key});

  @override
  State<GoalsPage> createState() => _GoalsPageState();
}

class _GoalsPageState extends State<GoalsPage> {
  late AsyncCubit<List<Goal>> _cubit;

  @override
  void initState() {
    super.initState();
    _cubit = AsyncCubit<List<Goal>>(const AsyncState())
      ..run(() => context.read<CarbonRepository>().goals());
  }

  void _reload() {
    _cubit.run(() => context.read<CarbonRepository>().goals(), silent: true);
  }

  @override
  void dispose() {
    _cubit.close();
    super.dispose();
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
              l10n.t('goalsTitle'),
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 2),
            Text(
              l10n.t('goalsSubtitle'),
              style: const TextStyle(fontSize: 11.5, color: AppColors.muted),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          await context.push('/goals/new');
          _reload();
        },
        backgroundColor: AppColors.forest,
        foregroundColor: Colors.white,
        icon: const Icon(Icons.add_rounded),
        label: Text(l10n.t('newGoal')),
      ),
      body: BlocProvider.value(
        value: _cubit,
        child: RefreshIndicator(
          onRefresh: () => _cubit.run(
            () => context.read<CarbonRepository>().goals(),
            silent: true,
          ),
          child: AsyncPageBody<List<Goal>>(
            onRetry: () => _cubit.run(() => context.read<CarbonRepository>().goals()),
            builder: (goals) {
              if (goals.isEmpty) {
                return ListView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  children: [
                    const SizedBox(height: 80),
                    EmptyState(
                      message: l10n.t('noGoals'),
                      icon: Icons.flag_outlined,
                      actionLabel: l10n.t('newGoal'),
                      onAction: () async {
                        await context.push('/goals/new');
                        _reload();
                      },
                    ),
                  ],
                );
              }
              return ListView.separated(
                padding: const EdgeInsets.fromLTRB(20, 8, 20, 100),
                itemCount: goals.length,
                separatorBuilder: (_, _) => const SizedBox(height: 12),
                itemBuilder: (context, index) => _GoalTile(goal: goals[index]),
              );
            },
          ),
        ),
      ),
    );
  }
}

class _GoalTile extends StatelessWidget {
  const _GoalTile({required this.goal});

  final Goal goal;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final locale = l10n.locale.languageCode;
    final active = goal.status == 'active';
    return CarbonCard(
      onTap: () => context.push('/goals/${goal.id}'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: const BoxDecoration(
                  color: AppColors.mint,
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.flag_rounded, color: AppColors.forest, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  goal.title,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
                ),
              ),
              Pill(
                label: active ? l10n.t('onTrack') : l10n.t(goal.status),
                color: active ? AppColors.mint : AppColors.cream,
                foreground: active ? AppColors.forest : AppColors.muted,
              ),
            ],
          ),
          const SizedBox(height: 18),
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          '${formatPercent(goal.achievedPercent, locale: locale)}',
                          style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
                        ),
                        const SizedBox(width: 5),
                        Text(
                          l10n.t('achieved'),
                          style: const TextStyle(fontSize: 10, color: AppColors.muted),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    MetricBar(value: goal.achievedPercent / 100),
                    const SizedBox(height: 9),
                    Text(
                      '${formatKg(goal.currentKg, locale: locale)} / ${formatKg(goal.targetKg, locale: locale)} ${l10n.t('kgCo2e')}',
                      textDirection: TextDirection.ltr,
                      style: const TextStyle(fontSize: 10, color: AppColors.muted),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 22),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '${goal.targetPercent.round()}%',
                    style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
                  ),
                  Text(
                    l10n.t('targetPercent'),
                    style: const TextStyle(fontSize: 9, color: AppColors.muted),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '${goal.daysLeft} ${l10n.t('daysLeft')}',
                    style: const TextStyle(fontSize: 9.5, color: AppColors.muted),
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }
}
