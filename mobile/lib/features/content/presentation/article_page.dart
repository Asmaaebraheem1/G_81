import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/async_cubit.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/models.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/app_widgets.dart';
import '../../dashboard/data/carbon_repository.dart';

class ArticlePage extends StatefulWidget {
  const ArticlePage({super.key, required this.slug});

  final String slug;

  @override
  State<ArticlePage> createState() => _ArticlePageState();
}

class _ArticlePageState extends State<ArticlePage> {
  late AsyncCubit<Article> _cubit;

  Future<Article> _load() =>
      context.read<CarbonRepository>().article(widget.slug);

  @override
  void initState() {
    super.initState();
    _cubit = AsyncCubit<Article>(const AsyncState())..run(_load);
  }

  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(context.tr('contentTitle'))),
      body: BlocProvider.value(
        value: _cubit,
        child: AsyncPageBody<Article>(
          onRetry: () => _cubit.run(_load),
          builder: (article) {
            final locale = context.l10n.locale.languageCode;
            final paragraphs = article
                .body(locale)
                .split('\n')
                .where((line) => line.trim().isNotEmpty)
                .toList();
            return ListView(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
              children: [
                Container(
                  height: 150,
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [AppColors.forest, AppColors.forestDeep],
                    ),
                    borderRadius: BorderRadius.circular(24),
                  ),
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      if (article.category.isNotEmpty)
                        Pill(
                          label: context.l10n.categoryLabel(article.category),
                          color: Colors.white.withValues(alpha: 0.14),
                          foreground: Colors.white,
                        ),
                      const Icon(
                        Icons.menu_book_rounded,
                        color: Colors.white54,
                        size: 30,
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
                Text(
                  article.title(locale),
                  style: const TextStyle(
                    fontSize: 25,
                    fontWeight: FontWeight.w800,
                    height: 1.2,
                    letterSpacing: -0.5,
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  article.summary(locale),
                  style: const TextStyle(
                    fontSize: 12.5,
                    height: 1.55,
                    color: AppColors.muted,
                  ),
                ),
                const SizedBox(height: 18),
                const Divider(),
                const SizedBox(height: 14),
                for (final paragraph in paragraphs) ...[
                  Text(
                    paragraph.replaceAll(RegExp(r'^#+\s*'), ''),
                    style: TextStyle(
                      fontSize: paragraph.startsWith('#') ? 15 : 12.5,
                      height: 1.65,
                      fontWeight: paragraph.startsWith('#') ? FontWeight.w700 : FontWeight.w400,
                    ),
                  ),
                  const SizedBox(height: 12),
                ],
              ],
            );
          },
        ),
      ),
    );
  }
}
