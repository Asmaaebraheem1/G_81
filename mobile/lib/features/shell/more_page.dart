import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../core/localization/app_localizations.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/app_widgets.dart';
import '../auth/presentation/auth_cubit.dart';

class MorePage extends StatelessWidget {
  const MorePage({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final user = context.watch<AuthCubit>().state.user;
    final explore = [
      (Icons.insights_rounded, l10n.t('insights'), '/insights', const Color(0xFF5B4B8A)),
      (Icons.route_outlined, l10n.t('plans'), '/plans', const Color(0xFF8C5A2B)),
      (Icons.flag_outlined, l10n.t('goals'), '/goals', const Color(0xFF3F6FA8)),
      (Icons.swap_horiz_rounded, l10n.t('alternatives'), '/alternatives', AppColors.forest),
      (Icons.emoji_events_outlined, l10n.t('challenges'), '/challenges', const Color(0xFFB38336)),
      (Icons.workspace_premium_outlined, l10n.t('achievements'), '/achievements', const Color(0xFF6A4B1F)),
      (Icons.leaderboard_outlined, l10n.t('leaderboard'), '/leaderboard', const Color(0xFF3F6FA8)),
      (Icons.upload_file_outlined, l10n.t('documents'), '/documents', AppColors.forest),
      (Icons.menu_book_outlined, l10n.t('content'), '/content', const Color(0xFF2A8465)),
    ];
    final account = [
      (Icons.notifications_none_rounded, l10n.t('notifications'), '/notifications'),
      (Icons.person_outline_rounded, l10n.t('settings'), '/settings'),
      if (user?.organizationId != null)
        (Icons.business_rounded, l10n.t('organization'), '/organization'),
    ];
    return Scaffold(
      appBar: AppBar(
        titleSpacing: 20,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              l10n.t('moreTitle'),
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 2),
            Text(
              l10n.t('moreSubtitle'),
              style: const TextStyle(fontSize: 11.5, color: AppColors.muted),
            ),
          ],
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
        children: [
          CarbonCard(
            onTap: () => context.push('/settings'),
            color: AppColors.forestDeep,
            child: Row(
              children: [
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.12),
                    shape: BoxShape.circle,
                  ),
                  child: Center(
                    child: Text(
                      (user?.fullName ?? '?').substring(0, 1).toUpperCase(),
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        user?.fullName ?? '—',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 14,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        user?.email ?? '',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.55),
                          fontSize: 9.5,
                        ),
                      ),
                    ],
                  ),
                ),
                const Icon(Icons.chevron_right_rounded, color: Colors.white54),
              ],
            ),
          ),
          const SizedBox(height: 24),
          SectionTitle(l10n.t('explore')),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 3,
              crossAxisSpacing: 9,
              mainAxisSpacing: 9,
              childAspectRatio: 0.94,
            ),
            itemCount: explore.length,
            itemBuilder: (context, index) => _MoreTile(
              icon: explore[index].$1,
              label: explore[index].$2,
              route: explore[index].$3,
              color: explore[index].$4,
            ),
          ),
          const SizedBox(height: 24),
          SectionTitle(l10n.t('account')),
          CarbonCard(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Column(
              children: [
                for (final item in account)
                  ListTile(
                    leading: Icon(item.$1, size: 21, color: AppColors.forest),
                    title: Text(
                      item.$2,
                      style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600),
                    ),
                    trailing: const Icon(Icons.chevron_right_rounded, size: 19),
                    onTap: () => context.push(item.$3),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 22),
          Text(
            '${l10n.t('appName')} · v1.0.0',
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 9.5, color: AppColors.muted),
          ),
        ],
      ),
    );
  }
}

class _MoreTile extends StatelessWidget {
  const _MoreTile({
    required this.icon,
    required this.label,
    required this.route,
    required this.color,
  });

  final IconData icon;
  final String label;
  final String route;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () => context.push(route),
      borderRadius: BorderRadius.circular(18),
      child: Container(
        padding: const EdgeInsets.all(11),
        decoration: BoxDecoration(
          color: AppColors.paper,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: AppColors.line),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 34,
              height: 34,
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.11),
                borderRadius: BorderRadius.circular(11),
              ),
              child: Icon(icon, size: 18, color: color),
            ),
            const Spacer(),
            Text(
              label,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600, height: 1.3),
            ),
          ],
        ),
      ),
    );
  }
}
