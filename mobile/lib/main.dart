import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'core/database/app_database.dart';
import 'core/localization/app_localizations.dart';
import 'core/navigation/app_router.dart';
import 'core/network/api_client.dart';
import 'core/storage/settings_store.dart';
import 'core/storage/token_store.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/data/auth_repository.dart';
import 'features/auth/presentation/auth_cubit.dart';
import 'features/dashboard/data/carbon_repository.dart';
import 'features/settings/presentation/settings_cubit.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final settingsStore = await SettingsStore.load();
  final settings = SettingsCubit(settingsStore);
  final tokens = SecureTokenStore();
  final api = ApiClient(tokenStore: tokens);
  final auth = AuthCubit(AuthRepository(api, tokens));
  api.onSessionExpired = auth.sessionExpired;
  final repository = CarbonRepository(
    api,
    cache: LocalCache(),
  );

  auth.bootstrap();

  runApp(
    CarbonWiseApp(
      auth: auth,
      settings: settings,
      repository: repository,
    ),
  );
}

class CarbonWiseApp extends StatefulWidget {
  const CarbonWiseApp({
    super.key,
    required this.auth,
    required this.settings,
    required this.repository,
  });

  final AuthCubit auth;
  final SettingsCubit settings;
  final CarbonRepository repository;

  @override
  State<CarbonWiseApp> createState() => _CarbonWiseAppState();
}

class _CarbonWiseAppState extends State<CarbonWiseApp> {
  late final _router = createRouter(widget.auth);

  @override
  Widget build(BuildContext context) {
    return MultiRepositoryProvider(
      providers: [
        RepositoryProvider<CarbonRepository>.value(value: widget.repository),
      ],
      child: MultiBlocProvider(
        providers: [
          BlocProvider<AuthCubit>.value(value: widget.auth),
          BlocProvider<SettingsCubit>.value(value: widget.settings),
        ],
        child: BlocBuilder<SettingsCubit, SettingsState>(
          buildWhen: (previous, current) =>
              previous.locale.languageCode != current.locale.languageCode,
          builder: (context, settings) {
            return MaterialApp.router(
              title: settings.isArabic ? 'كربونوايز' : 'CarbonWise',
              debugShowCheckedModeBanner: false,
              theme: AppTheme.light,
              routerConfig: _router,
              locale: settings.locale,
              supportedLocales: AppLocalizations.supportedLocales,
              localizationsDelegates: const [
                AppLocalizations.delegate,
                GlobalMaterialLocalizations.delegate,
                GlobalWidgetsLocalizations.delegate,
                GlobalCupertinoLocalizations.delegate,
              ],
              builder: (context, child) {
                return MediaQuery(
                  data: MediaQuery.of(context).copyWith(
                    textScaler: MediaQuery.textScalerOf(context).clamp(
                      minScaleFactor: 0.9,
                      maxScaleFactor: 1.15,
                    ),
                  ),
                  child: child ?? const SizedBox.shrink(),
                );
              },
            );
          },
        ),
      ),
    );
  }
}
