import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/app_localizations.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/app_widgets.dart';
import '../../dashboard/data/carbon_repository.dart';
import 'assistant_cubit.dart';

class AssistantPage extends StatefulWidget {
  const AssistantPage({super.key});

  @override
  State<AssistantPage> createState() => _AssistantPageState();
}

class _AssistantPageState extends State<AssistantPage> {
  final _controller = TextEditingController();
  final _scroll = ScrollController();

  @override
  void dispose() {
    _controller.dispose();
    _scroll.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scroll.hasClients) return;
      _scroll.animateTo(
        _scroll.position.maxScrollExtent + 80,
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeOut,
      );
    });
  }

  Future<void> _send(AssistantCubit cubit, String text) async {
    if (text.trim().isEmpty) return;
    _controller.clear();
    setState(() {});
    await cubit.send(text, context.l10n.locale.languageCode);
    _scrollToBottom();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return BlocProvider(
      create: (context) =>
          AssistantCubit(context.read<CarbonRepository>())..init(),
      child: Builder(
        builder: (context) {
          final cubit = context.read<AssistantCubit>();
          return Scaffold(
            appBar: AppBar(
              titleSpacing: 20,
              title: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    l10n.t('assistantTitle'),
                    style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    l10n.t('assistantSubtitle'),
                    style: const TextStyle(fontSize: 11.5, color: AppColors.muted),
                  ),
                ],
              ),
              actions: [
                IconButton(
                  onPressed: () => context.push('/insights'),
                  icon: const Icon(Icons.insights_rounded),
                ),
                const SizedBox(width: 8),
              ],
            ),
            body: BlocConsumer<AssistantCubit, AssistantState>(
              listenWhen: (previous, current) =>
                  previous.messages.length != current.messages.length ||
                  previous.sending != current.sending,
              listener: (context, state) => _scrollToBottom(),
              builder: (context, state) {
                return Column(
                  children: [
                    if (!state.loading && !state.enabled)
                      Container(
                        margin: const EdgeInsets.fromLTRB(20, 4, 20, 10),
                        padding: const EdgeInsets.all(13),
                        decoration: BoxDecoration(
                          color: AppColors.sandSoft,
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Icon(
                              Icons.power_off_rounded,
                              size: 17,
                              color: Color(0xFF8C5A2B),
                            ),
                            const SizedBox(width: 9),
                            Expanded(
                              child: Text(
                                l10n.t('aiDisabledBody'),
                                style: const TextStyle(
                                  fontSize: 10.5,
                                  height: 1.4,
                                  color: Color(0xFF6B451F),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    Expanded(
                      child: state.loading
                          ? const LoadingList(itemCount: 2)
                          : state.messages.isEmpty
                              ? _EmptyChat(
                                  suggestions: [
                                    l10n.t('suggestion1'),
                                    l10n.t('suggestion2'),
                                    l10n.t('suggestion3'),
                                  ],
                                  onSuggestion: (text) => _send(cubit, text),
                                )
                              : ListView.builder(
                                  controller: _scroll,
                                  padding: const EdgeInsets.fromLTRB(20, 10, 20, 18),
                                  itemCount: state.messages.length + (state.sending ? 1 : 0),
                                  itemBuilder: (context, index) {
                                    if (index == state.messages.length) {
                                      return const _TypingBubble();
                                    }
                                    return _MessageBubble(message: state.messages[index]);
                                  },
                                ),
                    ),
                    SafeArea(
                      top: false,
                      child: Container(
                        padding: const EdgeInsets.fromLTRB(16, 9, 16, 10),
                        decoration: const BoxDecoration(
                          color: AppColors.cream,
                          border: Border(top: BorderSide(color: AppColors.line)),
                        ),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            Expanded(
                              child: TextField(
                                controller: _controller,
                                minLines: 1,
                                maxLines: 4,
                                textInputAction: TextInputAction.send,
                                onSubmitted: (value) => _send(cubit, value),
                                onChanged: (_) => setState(() {}),
                                decoration: InputDecoration(
                                  hintText: l10n.t('askAnything'),
                                  contentPadding: const EdgeInsets.symmetric(
                                    horizontal: 15,
                                    vertical: 12,
                                  ),
                                  fillColor: AppColors.paper,
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            SizedBox(
                              width: 48,
                              height: 48,
                              child: IconButton.filled(
                                onPressed: state.sending || _controller.text.trim().isEmpty
                                    ? null
                                    : () => _send(cubit, _controller.text),
                                style: IconButton.styleFrom(
                                  backgroundColor: AppColors.forest,
                                  foregroundColor: Colors.white,
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(15),
                                  ),
                                ),
                                icon: const Icon(Icons.arrow_upward_rounded, size: 21),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                );
              },
            ),
          );
        },
      ),
    );
  }
}

class _EmptyChat extends StatelessWidget {
  const _EmptyChat({required this.suggestions, required this.onSuggestion});

  final List<String> suggestions;
  final ValueChanged<String> onSuggestion;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 20),
      children: [
        Center(
          child: Container(
            width: 80,
            height: 80,
            decoration: const BoxDecoration(
              color: AppColors.mint,
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.auto_awesome_rounded, color: AppColors.forest, size: 34),
          ),
        ),
        const SizedBox(height: 18),
        Text(
          l10n.t('assistantTitle'),
          textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 6),
        Text(
          l10n.t('assistantSubtitle'),
          textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 11.5, color: AppColors.muted),
        ),
        const SizedBox(height: 26),
        Text(
          l10n.t('suggestions'),
          style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: AppColors.muted),
        ),
        const SizedBox(height: 9),
        for (final suggestion in suggestions) ...[
          CarbonCard(
            onTap: () => onSuggestion(suggestion),
            padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 14),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    suggestion,
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
                  ),
                ),
                const Icon(Icons.north_east_rounded, size: 16, color: AppColors.muted),
              ],
            ),
          ),
          const SizedBox(height: 8),
        ],
        const SizedBox(height: 14),
        Text(
          l10n.isArabic
              ? 'الذكاء الاصطناعي يشرح أرقام الخادم فقط. لا يحسب الانبعاثات.'
              : 'AI explains the server numbers only. It never calculates emissions.',
          textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 9.5, color: AppColors.muted, height: 1.4),
        ),
      ],
    );
  }
}

class _MessageBubble extends StatelessWidget {
  const _MessageBubble({required this.message});

  final ChatMessage message;

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == 'user';
    return Align(
      alignment: isUser
          ? AlignmentDirectional.centerEnd
          : AlignmentDirectional.centerStart,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.sizeOf(context).width * 0.82,
        ),
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 12),
        decoration: BoxDecoration(
          color: isUser ? AppColors.forest : AppColors.paper,
          borderRadius: BorderRadiusDirectional.only(
            topStart: const Radius.circular(18),
            topEnd: const Radius.circular(18),
            bottomStart: Radius.circular(isUser ? 18 : 4),
            bottomEnd: Radius.circular(isUser ? 4 : 18),
          ),
          border: isUser ? null : Border.all(color: AppColors.line),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (!isUser && message.isFallback)
              Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Pill(
                  label: context.tr('backendNumbers'),
                  icon: Icons.dataset_outlined,
                ),
              ),
            Text(
              message.content,
              style: TextStyle(
                fontSize: 12.5,
                height: 1.55,
                color: isUser ? Colors.white : AppColors.ink,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _TypingBubble extends StatelessWidget {
  const _TypingBubble();

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: AlignmentDirectional.centerStart,
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: AppColors.paper,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: AppColors.line),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(
              width: 13,
              height: 13,
              child: CircularProgressIndicator(strokeWidth: 1.8),
            ),
            const SizedBox(width: 9),
            Text(
              context.tr('thinking'),
              style: const TextStyle(fontSize: 11, color: AppColors.muted),
            ),
          ],
        ),
      ),
    );
  }
}
