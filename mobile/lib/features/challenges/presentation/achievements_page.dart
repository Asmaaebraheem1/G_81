import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../core/async_cubit.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/models.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/app_widgets.dart';
import '../../dashboard/data/carbon_repository.dart';

class AchievementsPage extends StatefulWidget {
  const AchievementsPage({super.key});

  @override
  State<AchievementsPage> createState() => _AchievementsPageState();
}

class _AchievementsPageState extends State<AchievementsPage> {
  late AsyncCubit<Map<String, dynamic>> _cubit;

  Future<Map<String, dynamic>> _load() =>
      context.read<CarbonRepository>().achievements();

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

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return Scaffold(
      appBar: AppBar(
        title: Text(
          l10n.t('achievements'),
          style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
        ),
        actions: [
          IconButton(
            onPressed: () => context.push('/leaderboard'),
            icon: const Icon(Icons.leaderboard_outlined),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: BlocProvider.value(
        value: _cubit,
        child: AsyncPageBody<Map<String, dynamic>>(
          onRetry: () => _cubit.run(_load),
          builder: (data) {
            final locale = l10n.locale.languageCode;
            final earned = maps(data['badges']);
            final all = maps(data['all_badges']);
            final milestones = map(data['milestones']);
            final earnedIds = earned.map((badge) => ni(badge['id'])).toSet();
            return ListView(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
              children: [
                Container(
                  padding: const EdgeInsets.all(22),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [Color(0xFF6A4B1F), Color(0xFFB38336)],
                    ),
                    borderRadius: BorderRadius.circular(26),
                  ),
                  child: Row(
                    children: [
                      Container(
                        width: 54,
                        height: 54,
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.14),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(
                          Icons.workspace_premium_rounded,
                          color: Colors.white,
                          size: 28,
                        ),
                      ),
                      const SizedBox(width: 15),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '${ni(data['points'])} ${l10n.t('points')}',
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 26,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                            Text(
                              '${earned.length} / ${all.length} ${l10n.t('badges')}',
                              style: TextStyle(
                                color: Colors.white.withValues(alpha: 0.65),
                                fontSize: 11,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 22),
                SectionTitle(l10n.t('progress')),
                Row(
                  children: [
                    Expanded(
                      child: _MilestoneTile(
                        icon: Icons.receipt_long_outlined,
                        value: '${ni(milestones['records'])}',
                        label: l10n.t('records'),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: _MilestoneTile(
                        icon: Icons.flag_outlined,
                        value: '${ni(milestones['goals_completed'])}',
                        label: l10n.t('goals'),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: _MilestoneTile(
                        icon: Icons.route_outlined,
                        value: '${ni(milestones['plans_completed'])}',
                        label: l10n.t('plans'),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: _MilestoneTile(
                        icon: Icons.emoji_events_outlined,
                        value: '${ni(milestones['challenges_completed'])}',
                        label: l10n.t('challenges'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                SectionTitle(l10n.t('badges')),
                if (all.isEmpty)
                  CarbonCard(
                    child: Text(
                      l10n.t('noData'),
                      style: const TextStyle(color: AppColors.muted),
                    ),
                  )
                else
                  GridView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      crossAxisSpacing: 10,
                      mainAxisSpacing: 10,
                      childAspectRatio: 1.55,
                    ),
                    itemCount: all.length,
                    itemBuilder: (context, index) {
                      final badge = all[index];
                      final owned = earnedIds.contains(ni(badge['id']));
                      return Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: owned ? AppColors.paper : AppColors.cream,
                          borderRadius: BorderRadius.circular(18),
                          border: Border.all(
                            color: owned ? AppColors.sand : AppColors.line,
                          ),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Icon(
                              owned ? Icons.workspace_premium_rounded : Icons.lock_outline_rounded,
                              color: owned ? AppColors.sand : AppColors.muted,
                              size: 22,
                            ),
                            const Spacer(),
                            Text(
                              locale == 'ar' ? s(badge['title_ar']) : s(badge['title_en']),
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: TextStyle(
                                fontSize: 10.5,
                                fontWeight: FontWeight.w700,
                                color: owned ? AppColors.ink : AppColors.muted,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              '${ni(badge['points'])} ${l10n.t('points')}',
                              style: const TextStyle(fontSize: 8.5, color: AppColors.muted),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _MilestoneTile extends StatelessWidget {
  const _MilestoneTile({required this.icon, required this.value, required this.label});

  final IconData icon;
  final String value;
  final String label;

  @override
  Widget build(BuildContext context) {
    return CarbonCard(
      padding: const EdgeInsets.symmetric(vertical: 13, horizontal: 8),
      child: Column(
        children: [
          Icon(icon, size: 17, color: AppColors.forest),
          const SizedBox(height: 6),
          Text(
            value,
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontSize: 8, color: AppColors.muted),
          ),
        ],
      ),
    );
  }
}
