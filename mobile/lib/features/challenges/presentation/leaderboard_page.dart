import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../core/async_cubit.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/models.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/app_widgets.dart';
import '../../dashboard/data/carbon_repository.dart';

class LeaderboardPage extends StatefulWidget {
  const LeaderboardPage({super.key});

  @override
  State<LeaderboardPage> createState() => _LeaderboardPageState();
}

class _LeaderboardPageState extends State<LeaderboardPage> {
  String _period = 'month';
  late AsyncCubit<Map<String, dynamic>> _cubit;

  Future<Map<String, dynamic>> _load() =>
      context.read<CarbonRepository>().leaderboard(period: _period);

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
          l10n.t('leaderboard'),
          style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
        ),
      ),
      body: BlocProvider.value(
        value: _cubit,
        child: AsyncPageBody<Map<String, dynamic>>(
          onRetry: () => _cubit.run(_load),
          builder: (data) {
            final entries = maps(data['entries']);
            final optedIn = data['opt_in'] == true;
            return ListView(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
              children: [
                PeriodSelector(
                  value: _period,
                  onChanged: (period) {
                    setState(() => _period = period);
                    _cubit.run(_load);
                  },
                ),
                const SizedBox(height: 16),
                if (!optedIn)
                  CarbonCard(
                    color: AppColors.sandSoft,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.visibility_off_outlined, size: 19, color: Color(0xFF8C5A2B)),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                l10n.t('notOptedIn'),
                                style: const TextStyle(fontWeight: FontWeight.w700),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          l10n.isArabic
                              ? 'لا تظهر سوى الأسماء المستعارة للمستخدمين الموافقين. لا يتم عرض البريد الإلكتروني أبدًا.'
                              : 'Only opted-in users appear. Aliases are shown; emails are never displayed.',
                          style: const TextStyle(fontSize: 10.5, height: 1.4, color: Color(0xFF6B451F)),
                        ),
                        const SizedBox(height: 12),
                        FilledButton(
                          onPressed: () => context.push('/settings'),
                          style: FilledButton.styleFrom(minimumSize: const Size(0, 42)),
                          child: Text(l10n.t('optIn')),
                        ),
                      ],
                    ),
                  )
                else if (entries.isEmpty)
                  EmptyState(message: l10n.t('noData'), icon: Icons.leaderboard_outlined)
                else ...[
                  SectionTitle(l10n.t('yourRank')),
                  CarbonCard(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Column(
                      children: [
                        for (var i = 0; i < entries.length; i++) ...[
                          _LeaderRow(entry: entries[i]),
                          if (i != entries.length - 1)
                            const Divider(height: 1, indent: 56, endIndent: 16),
                        ],
                      ],
                    ),
                  ),
                ],
                const SizedBox(height: 14),
                Text(
                  l10n.isArabic
                      ? 'لا يظهر سوى المستخدمين الذين وافقوا على الظهور. تُعرض الأسماء المستعارة بدلًا من البريد الإلكتروني.'
                      : s(data['note']),
                  style: const TextStyle(fontSize: 9.5, color: AppColors.muted, height: 1.4),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _LeaderRow extends StatelessWidget {
  const _LeaderRow({required this.entry});

  final Map<String, dynamic> entry;

  @override
  Widget build(BuildContext context) {
    final isMe = entry['is_me'] == true;
    final rank = ni(entry['rank']);
    return Container(
      color: isMe ? AppColors.mint.withValues(alpha: 0.55) : Colors.transparent,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          SizedBox(
            width: 32,
            child: Text(
              rank <= 3 ? ['🥇', '🥈', '🥉'][rank - 1] : '$rank',
              style: TextStyle(
                fontSize: rank <= 3 ? 17 : 12,
                fontWeight: FontWeight.w800,
                color: AppColors.muted,
              ),
            ),
          ),
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              color: isMe ? AppColors.forest : AppColors.cream,
              shape: BoxShape.circle,
            ),
            child: Center(
              child: Text(
                s(entry['alias']).isEmpty ? '?' : s(entry['alias']).substring(0, 1).toUpperCase(),
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w800,
                  color: isMe ? Colors.white : AppColors.forest,
                ),
              ),
            ),
          ),
          const SizedBox(width: 11),
          Expanded(
            child: BidiText(
              s(entry['alias']),
              textAlign: TextAlign.right,
              style: TextStyle(
                fontSize: 12,
                fontWeight: isMe ? FontWeight.w800 : FontWeight.w500,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Text(
            '${ni(entry['points'])}',
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w800),
          ),
          const SizedBox(width: 4),
          Text(
            context.tr('points'),
            style: const TextStyle(fontSize: 8, color: AppColors.muted),
          ),
        ],
      ),
    );
  }
}
