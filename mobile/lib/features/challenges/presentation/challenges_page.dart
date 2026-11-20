import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../core/async_cubit.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/models.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/app_widgets.dart';
import '../../dashboard/data/carbon_repository.dart';

class ChallengesPage extends StatefulWidget {
  const ChallengesPage({super.key});

  @override
  State<ChallengesPage> createState() => _ChallengesPageState();
}

class _ChallengesPageState extends State<ChallengesPage> {
  String _filter = 'active';
  late AsyncCubit<List<Challenge>> _cubit;

  Future<List<Challenge>> _load() => context.read<CarbonRepository>().challenges();

  @override
  void initState() {
    super.initState();
    _cubit = AsyncCubit<List<Challenge>>(const AsyncState())..run(_load);
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
              l10n.t('challengesTitle'),
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 2),
            Text(
              l10n.t('challengesSubtitle'),
              style: const TextStyle(fontSize: 11.5, color: AppColors.muted),
            ),
          ],
        ),
        actions: [
          IconButton(
            onPressed: () => context.push('/achievements'),
            icon: const Icon(Icons.workspace_premium_outlined),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: BlocProvider.value(
        value: _cubit,
        child: AsyncPageBody<List<Challenge>>(
          onRetry: () => _cubit.run(_load),
          builder: (challenges) {
            final filtered = challenges.where((c) => c.status == _filter).toList();
            return Column(
              children: [
                SizedBox(
                  height: 46,
                  child: ListView(
                    scrollDirection: Axis.horizontal,
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    children: [
                      for (final item in const [
                        ('active', 'challengesTitle'),
                        ('upcoming', 'pending'),
                        ('completed', 'completed'),
                      ]) ...[
                        ChoiceChip(
                          label: Text(l10n.t(item.$2)),
                          selected: _filter == item.$1,
                          showCheckmark: false,
                          onSelected: (_) => setState(() => _filter = item.$1),
                        ),
                        const SizedBox(width: 8),
                      ],
                    ],
                  ),
                ),
                Expanded(
                  child: filtered.isEmpty
                      ? EmptyState(
                          message: l10n.t('noChallenges'),
                          icon: Icons.emoji_events_outlined,
                        )
                      : ListView.separated(
                          padding: const EdgeInsets.fromLTRB(20, 8, 20, 30),
                          itemCount: filtered.length,
                          separatorBuilder: (_, _) => const SizedBox(height: 11),
                          itemBuilder: (context, index) =>
                              _ChallengeCard(challenge: filtered[index]),
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

class _ChallengeCard extends StatelessWidget {
  const _ChallengeCard({required this.challenge});

  final Challenge challenge;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final locale = l10n.locale.languageCode;
    return CarbonCard(
      onTap: () => context.push('/challenges/${challenge.id}'),
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
                child: const Icon(Icons.emoji_events_rounded, color: Color(0xFF8C5A2B), size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      challenge.title(locale),
                      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      challenge.description(locale),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 10.5, color: AppColors.muted),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Pill(
                label: '${challenge.points} ${l10n.t('points')}',
                color: AppColors.mint,
                foreground: AppColors.forest,
              ),
              const SizedBox(width: 7),
              Pill(
                label: challenge.joined ? l10n.t('joined') : l10n.t(challenge.status),
                color: challenge.joined ? AppColors.sandSoft : AppColors.cream,
                foreground: challenge.joined ? const Color(0xFF8C5A2B) : AppColors.muted,
              ),
              const Spacer(),
              Text(
                '${challenge.progressValue.round()} / ${challenge.targetValue.round()}',
                textDirection: TextDirection.ltr,
                style: const TextStyle(fontSize: 10.5, color: AppColors.muted),
              ),
            ],
          ),
          const SizedBox(height: 8),
          MetricBar(
            value: challenge.targetValue <= 0
                ? 0
                : challenge.progressValue / challenge.targetValue,
            color: AppColors.sand,
          ),
        ],
      ),
    );
  }
}
