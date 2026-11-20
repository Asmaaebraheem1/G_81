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

class NotificationsPage extends StatefulWidget {
  const NotificationsPage({super.key});

  @override
  State<NotificationsPage> createState() => _NotificationsPageState();
}

class _NotificationsPageState extends State<NotificationsPage> {
  late AsyncCubit<Map<String, dynamic>> _cubit;

  Future<Map<String, dynamic>> _load() =>
      context.read<CarbonRepository>().notifications();

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

  Future<void> _markAll() async {
    try {
      await context.read<CarbonRepository>().markAllNotificationsRead();
      if (!mounted) return;
      _cubit.run(_load, silent: true);
    } catch (error) {
      if (!mounted) return;
      showSnack(context, error.toString(), error: true);
    }
  }

  Future<void> _open(AppNotification notification) async {
    if (!notification.isRead) {
      try {
        await context.read<CarbonRepository>().markNotificationRead(notification.id);
        if (mounted) _cubit.run(_load, silent: true);
      } catch (_) {}
    }
    if (!mounted) return;
    final url = notification.actionUrl;
    if (url.startsWith('/challenges/')) {
      final id = int.tryParse(url.split('/').last);
      if (id != null) context.push('/challenges/$id');
    } else if (url.startsWith('/plans/')) {
      final id = int.tryParse(url.split('/').last);
      if (id != null) context.push('/plans/$id');
    } else if (url.startsWith('/goals/')) {
      final id = int.tryParse(url.split('/').last);
      if (id != null) context.push('/goals/$id');
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return Scaffold(
      appBar: AppBar(
        title: Text(
          l10n.t('notificationsTitle'),
          style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
        ),
        actions: [
          IconButton(
            onPressed: _markAll,
            tooltip: l10n.t('markAllRead'),
            icon: const Icon(Icons.done_all_rounded),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: BlocProvider.value(
        value: _cubit,
        child: AsyncPageBody<Map<String, dynamic>>(
          onRetry: () => _cubit.run(_load),
          builder: (data) {
            final items = maps(data['notifications']).map(AppNotification.fromJson).toList();
            if (items.isEmpty) {
              return EmptyState(
                message: l10n.t('noNotifications'),
                icon: Icons.notifications_none_rounded,
              );
            }
            return ListView.separated(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 30),
              itemCount: items.length,
              separatorBuilder: (_, _) => const SizedBox(height: 9),
              itemBuilder: (context, index) => _NotificationTile(
                notification: items[index],
                onTap: () => _open(items[index]),
              ),
            );
          },
        ),
      ),
    );
  }
}

class _NotificationTile extends StatelessWidget {
  const _NotificationTile({required this.notification, required this.onTap});

  final AppNotification notification;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final locale = context.l10n.locale.languageCode;
    return CarbonCard(
      onTap: onTap,
      color: notification.isRead ? AppColors.paper : AppColors.mint.withValues(alpha: 0.55),
      padding: const EdgeInsets.all(15),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 34,
            height: 34,
            decoration: const BoxDecoration(
              color: AppColors.mint,
              shape: BoxShape.circle,
            ),
            child: Icon(
              switch (notification.type) {
                'challenge' => Icons.emoji_events_outlined,
                'goal' => Icons.flag_outlined,
                'alert' => Icons.warning_amber_rounded,
                _ => Icons.notifications_none_rounded,
              },
              size: 17,
              color: AppColors.forest,
            ),
          ),
          const SizedBox(width: 11),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        notification.title(locale),
                        style: TextStyle(
                          fontSize: 12.5,
                          fontWeight: notification.isRead ? FontWeight.w600 : FontWeight.w800,
                        ),
                      ),
                    ),
                    if (!notification.isRead)
                      Container(
                        width: 7,
                        height: 7,
                        decoration: const BoxDecoration(
                          color: AppColors.sand,
                          shape: BoxShape.circle,
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  notification.body(locale),
                  style: const TextStyle(fontSize: 10.5, height: 1.45, color: AppColors.muted),
                ),
                const SizedBox(height: 5),
                Text(
                  formatDateTime(notification.createdAt, locale: locale),
                  style: const TextStyle(fontSize: 8.5, color: AppColors.muted),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
