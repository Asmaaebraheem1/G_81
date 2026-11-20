import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/format.dart';
import '../../../core/models.dart';
import '../../../core/network/api_exception.dart';
import '../../dashboard/data/carbon_repository.dart';

class ChatMessage extends Equatable {
  const ChatMessage({
    required this.role,
    required this.content,
    this.isFallback = false,
  });

  final String role;
  final String content;
  final bool isFallback;

  @override
  List<Object?> get props => [role, content, isFallback];
}

class AssistantState extends Equatable {
  const AssistantState({
    this.loading = true,
    this.enabled = false,
    this.sending = false,
    this.model = 'openrouter/free',
    this.remainingTokens,
    this.messages = const [],
    this.conversationId,
    this.error,
  });

  final bool loading;
  final bool enabled;
  final bool sending;
  final String model;
  final int? remainingTokens;
  final List<ChatMessage> messages;
  final int? conversationId;
  final String? error;

  AssistantState copyWith({
    bool? loading,
    bool? enabled,
    bool? sending,
    String? model,
    int? remainingTokens,
    List<ChatMessage>? messages,
    int? conversationId,
    String? error,
    bool clearError = false,
  }) {
    return AssistantState(
      loading: loading ?? this.loading,
      enabled: enabled ?? this.enabled,
      sending: sending ?? this.sending,
      model: model ?? this.model,
      remainingTokens: remainingTokens ?? this.remainingTokens,
      messages: messages ?? this.messages,
      conversationId: conversationId ?? this.conversationId,
      error: clearError ? null : (error ?? this.error),
    );
  }

  @override
  List<Object?> get props =>
      [loading, enabled, sending, model, remainingTokens, messages, conversationId, error];
}

class AssistantCubit extends Cubit<AssistantState> {
  AssistantCubit(this._repository) : super(const AssistantState());

  final CarbonRepository _repository;

  Future<void> init() async {
    try {
      final status = await _repository.aiStatus();
      final budget = map(status['budget']);
      emit(
        state.copyWith(
          loading: false,
          enabled: status['enabled'] == true,
          model: s(status['model'], 'openrouter/free'),
          remainingTokens: ni(budget['remaining']),
        ),
      );
    } catch (error) {
      emit(state.copyWith(loading: false, error: _friendly(error)));
    }
  }

  Future<void> send(String text, String locale) async {
    final message = text.trim();
    if (message.isEmpty || state.sending) return;
    final next = [
      ...state.messages,
      ChatMessage(role: 'user', content: message),
    ];
    emit(state.copyWith(messages: next, sending: true, clearError: true));
    try {
      final data = await _repository.aiChat(
        message: message,
        conversationId: state.conversationId,
        locale: locale,
      );
      emit(
        state.copyWith(
          sending: false,
          conversationId: ni(data['conversation_id']),
          messages: [
            ...next,
            ChatMessage(role: 'assistant', content: s(data['content'])),
          ],
        ),
      );
    } on ApiException catch (error) {
      if (error.isAiDisabled) {
        final fallback = map(error.details['fallback']);
        final totals = map(fallback['totals']);
        final totalKg = fallback['total_kg'] ?? totals['emissions_kg'];
        final categories = maps(fallback['top_categories']);
        final top = categories.isEmpty ? null : categories.first;
        final response = StringBuffer()
          ..writeln(
            locale == 'ar'
                ? 'المحادثة غير مفعّلة لأن مفتاح OpenRouter غير مضبوط. هذه أرقامك المحسوبة في الخادم:'
                : 'Chat is disabled because the OpenRouter key is not configured. Here is your backend-calculated data:',
          )
          ..writeln()
          ..writeln(
            '• ${locale == 'ar' ? 'الإجمالي' : 'Total'}: '
            '${formatKg(n(totalKg))} kg CO₂e',
          );
        if (top != null) {
          response.writeln(
            '• ${locale == 'ar' ? 'أكبر فئة' : 'Top category'}: '
            '${locale == 'ar' ? s(top['name_ar']) : s(top['name_en'])} '
            '(${s(top['share_percent'])}%)',
          );
        }
        response.writeln(
          locale == 'ar'
              ? '\nيمكنك فتح الرؤى لرؤية ملخص قائم على القواعد.'
              : '\nOpen Insights for a rules-based summary.',
        );
        emit(
          state.copyWith(
            sending: false,
            messages: [
              ...next,
              ChatMessage(role: 'assistant', content: response.toString(), isFallback: true),
            ],
          ),
        );
      } else {
        emit(
          state.copyWith(
            sending: false,
            messages: [
              ...next,
              ChatMessage(role: 'assistant', content: error.message, isFallback: true),
            ],
          ),
        );
      }
    } catch (error) {
      emit(
        state.copyWith(
          sending: false,
          messages: [
            ...next,
            ChatMessage(role: 'assistant', content: _friendly(error), isFallback: true),
          ],
        ),
      );
    }
  }

  void clearError() => emit(state.copyWith(clearError: true));

  String _friendly(Object error) {
    if (error is ApiException) return error.message;
    final raw = error.toString();
    if (raw.startsWith('ApiException')) {
      final index = raw.indexOf('): ');
      if (index > -1) return raw.substring(index + 3);
    }
    return raw;
  }
}
