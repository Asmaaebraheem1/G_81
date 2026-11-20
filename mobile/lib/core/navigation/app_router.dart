import 'dart:async';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../features/alternatives/presentation/alternatives_page.dart';
import '../../features/assistant/presentation/assistant_page.dart';
import '../../features/assistant/presentation/insights_page.dart';
import '../../features/auth/presentation/auth_cubit.dart';
import '../../features/auth/presentation/login_page.dart';
import '../../features/auth/presentation/register_page.dart';
import '../../features/auth/presentation/splash_page.dart';
import '../../features/auth/presentation/welcome_page.dart';
import '../../features/challenges/presentation/achievements_page.dart';
import '../../features/challenges/presentation/challenge_detail_page.dart';
import '../../features/challenges/presentation/challenges_page.dart';
import '../../features/challenges/presentation/leaderboard_page.dart';
import '../../features/content/presentation/article_page.dart';
import '../../features/content/presentation/content_page.dart';
import '../../features/dashboard/presentation/dashboard_page.dart';
import '../../features/documents/presentation/documents_page.dart';
import '../../features/goals/presentation/goal_detail_page.dart';
import '../../features/goals/presentation/goal_form_page.dart';
import '../../features/goals/presentation/goals_page.dart';
import '../../features/notifications/presentation/notifications_page.dart';
import '../../features/organization/presentation/organization_page.dart';
import '../../features/plans/presentation/plan_detail_page.dart';
import '../../features/plans/presentation/plans_page.dart';
import '../../features/records/presentation/record_detail_page.dart';
import '../../features/records/presentation/record_form_page.dart';
import '../../features/records/presentation/records_page.dart';
import '../../features/reports/presentation/reports_page.dart';
import '../../features/settings/presentation/settings_page.dart';
import '../../features/shell/app_shell.dart';
import '../../features/shell/more_page.dart';

GoRouter createRouter(AuthCubit auth) {
  final refresh = GoRouterRefreshStream(auth.stream);
  return GoRouter(
    initialLocation: '/',
    refreshListenable: refresh,
    redirect: (context, state) {
      final status = auth.state.status;
      final path = state.uri.path;
      final isPublic = path == '/' || path == '/login' || path == '/register';
      final isSplash = path == '/splash';

      if (status == AuthStatus.unknown) {
        return isSplash ? null : '/splash';
      }
      if (isSplash) {
        return status == AuthStatus.authenticated ? '/home' : '/';
      }
      if (status != AuthStatus.authenticated && !isPublic) {
        return '/login';
      }
      if (status == AuthStatus.authenticated && isPublic) {
        return '/home';
      }
      return null;
    },
    routes: [
      GoRoute(path: '/', builder: (context, state) => const WelcomePage()),
      GoRoute(path: '/splash', builder: (context, state) => const SplashPage()),
      GoRoute(path: '/login', builder: (context, state) => const LoginPage()),
      GoRoute(path: '/register', builder: (context, state) => const RegisterPage()),
      ShellRoute(
        builder: (context, state, child) => AppShell(child: child),
        routes: [
          GoRoute(path: '/home', builder: (context, state) => const DashboardPage()),
          GoRoute(
            path: '/records',
            builder: (context, state) => const RecordsPage(),
            routes: [
              GoRoute(
                path: 'new',
                builder: (context, state) => const RecordFormPage(),
              ),
              GoRoute(
                path: ':id',
                builder: (context, state) => RecordDetailPage(
                  recordId: int.tryParse(state.pathParameters['id'] ?? '') ?? 0,
                ),
                routes: [
                  GoRoute(
                    path: 'edit',
                    builder: (context, state) => RecordFormPage(
                      recordId: int.tryParse(state.pathParameters['id'] ?? ''),
                    ),
                  ),
                ],
              ),
            ],
          ),
          GoRoute(path: '/reports', builder: (context, state) => const ReportsPage()),
          GoRoute(path: '/assistant', builder: (context, state) => const AssistantPage()),
          GoRoute(path: '/insights', builder: (context, state) => const InsightsPage()),
          GoRoute(
            path: '/goals',
            builder: (context, state) => const GoalsPage(),
            routes: [
              GoRoute(path: 'new', builder: (context, state) => const GoalFormPage()),
              GoRoute(
                path: ':id',
                builder: (context, state) => GoalDetailPage(
                  goalId: int.tryParse(state.pathParameters['id'] ?? '') ?? 0,
                ),
              ),
            ],
          ),
          GoRoute(
            path: '/plans',
            builder: (context, state) => const PlansPage(),
            routes: [
              GoRoute(
                path: ':id',
                builder: (context, state) => PlanDetailPage(
                  planId: int.tryParse(state.pathParameters['id'] ?? '') ?? 0,
                ),
              ),
            ],
          ),
          GoRoute(
            path: '/alternatives',
            builder: (context, state) => const AlternativesPage(),
          ),
          GoRoute(
            path: '/challenges',
            builder: (context, state) => const ChallengesPage(),
            routes: [
              GoRoute(
                path: ':id',
                builder: (context, state) => ChallengeDetailPage(
                  challengeId: int.tryParse(state.pathParameters['id'] ?? '') ?? 0,
                ),
              ),
            ],
          ),
          GoRoute(
            path: '/achievements',
            builder: (context, state) => const AchievementsPage(),
          ),
          GoRoute(
            path: '/leaderboard',
            builder: (context, state) => const LeaderboardPage(),
          ),
          GoRoute(
            path: '/notifications',
            builder: (context, state) => const NotificationsPage(),
          ),
          GoRoute(path: '/settings', builder: (context, state) => const SettingsPage()),
          GoRoute(
            path: '/organization',
            builder: (context, state) => const OrganizationPage(),
          ),
          GoRoute(path: '/documents', builder: (context, state) => const DocumentsPage()),
          GoRoute(
            path: '/content',
            builder: (context, state) => const ContentPage(),
            routes: [
              GoRoute(
                path: ':slug',
                builder: (context, state) => ArticlePage(
                  slug: state.pathParameters['slug'] ?? '',
                ),
              ),
            ],
          ),
          GoRoute(path: '/more', builder: (context, state) => const MorePage()),
        ],
      ),
    ],
  );
}

class GoRouterRefreshStream extends ChangeNotifier {
  GoRouterRefreshStream(Stream<dynamic> stream) {
    _subscription = stream.asBroadcastStream().listen((_) => notifyListeners());
  }

  late final StreamSubscription<dynamic> _subscription;

  @override
  void dispose() {
    _subscription.cancel();
    super.dispose();
  }
}
