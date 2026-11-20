import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../core/async_cubit.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/models.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/app_widgets.dart';
import '../../dashboard/data/carbon_repository.dart';

class ContentPage extends StatefulWidget {
  const ContentPage({super.key});

  @override
  State<ContentPage> createState() => _ContentPageState();
}

class _ContentPageState extends State<ContentPage> {
  late AsyncCubit<List<Article>> _cubit;

  Future<List<Article>> _load() => context.read<CarbonRepository>().articles();

  @override
  void initState() {
    super.initState();
    _cubit = AsyncCubit<List<Article>>(const AsyncState())..run(_load);
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
              l10n.t('contentTitle'),
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 2),
            Text(
              l10n.t('contentSubtitle'),
              style: const TextStyle(fontSize: 11.5, color: AppColors.muted),
            ),
          ],
        ),
      ),
      body: BlocProvider.value(
        value: _cubit,
        child: AsyncPageBody<List<Article>>(
          onRetry: () => _cubit.run(_load),
          builder: (articles) {
            if (articles.isEmpty) {
              return EmptyState(message: l10n.t('noArticles'), icon: Icons.menu_book_outlined);
            }
            final locale = l10n.locale.languageCode;
            return ListView.separated(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 30),
              itemCount: articles.length,
              separatorBuilder: (_, _) => const SizedBox(height: 11),
              itemBuilder: (context, index) {
                final article = articles[index];
                final gradients = [
                  [const Color(0xFF2A8465), const Color(0xFF0E5C46)],
                  [const Color(0xFFB38336), const Color(0xFF6A4B1F)],
                  [const Color(0xFF3F6FA8), const Color(0xFF27466B)],
                ];
                final colors = gradients[index % gradients.length];
                return CarbonCard(
                  onTap: () => context.push('/content/${article.slug}'),
                  padding: EdgeInsets.zero,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        height: 94,
                        width: double.infinity,
                        decoration: BoxDecoration(
                          gradient: LinearGradient(colors: colors),
                          borderRadius: const BorderRadius.vertical(top: Radius.circular(21)),
                        ),
                        padding: const EdgeInsets.all(16),
                        child: Align(
                          alignment: AlignmentDirectional.topStart,
                          child: Icon(
                            Icons.menu_book_rounded,
                            color: Colors.white.withValues(alpha: 0.75),
                            size: 26,
                          ),
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.all(15),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            if (article.category.isNotEmpty)
                              Pill(label: l10n.categoryLabel(article.category), color: AppColors.mint),
                            const SizedBox(height: 8),
                            Text(
                              article.title(locale),
                              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w800),
                            ),
                            const SizedBox(height: 5),
                            Text(
                              article.summary(locale),
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                fontSize: 10.5,
                                height: 1.45,
                                color: AppColors.muted,
                              ),
                            ),
                            const SizedBox(height: 8),
                            Row(
                              children: [
                                Text(
                                  l10n.t('readMore'),
                                  style: const TextStyle(
                                    fontSize: 10.5,
                                    fontWeight: FontWeight.w700,
                                    color: AppColors.forest,
                                  ),
                                ),
                                const SizedBox(width: 4),
                                const Icon(
                                  Icons.arrow_forward_rounded,
                                  size: 14,
                                  color: AppColors.forest,
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                );
              },
            );
          },
        ),
      ),
    );
  }
}
