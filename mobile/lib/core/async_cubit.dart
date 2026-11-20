import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

enum AsyncStatus { idle, loading, ready, error }

class AsyncState<T> extends Equatable {
  const AsyncState({
    this.status = AsyncStatus.idle,
    this.data,
    this.error,
    this.fromCache = false,
  });

  final AsyncStatus status;
  final T? data;
  final String? error;
  final bool fromCache;

  bool get isLoading => status == AsyncStatus.loading;
  bool get hasData => data != null;

  AsyncState<T> copyWith({
    AsyncStatus? status,
    T? data,
    String? error,
    bool? fromCache,
    bool clearError = false,
  }) {
    return AsyncState<T>(
      status: status ?? this.status,
      data: data ?? this.data,
      error: clearError ? null : (error ?? this.error),
      fromCache: fromCache ?? this.fromCache,
    );
  }

  @override
  List<Object?> get props => [status, data, error, fromCache];
}

/// A tiny reusable BLoC for one-shot reads, while feature-specific logic
/// (chat, auth, settings) gets a dedicated cubit.
class AsyncCubit<T> extends Cubit<AsyncState<T>> {
  AsyncCubit(super.initial);

  Future<void> run(
    Future<T> Function() task, {
    bool keepData = true,
    bool silent = false,
  }) async {
    if (!silent) {
      emit(
        AsyncState<T>(
          status: AsyncStatus.loading,
          data: keepData ? state.data : null,
          fromCache: state.fromCache,
        ),
      );
    }
    try {
      final data = await task();
      emit(AsyncState<T>(status: AsyncStatus.ready, data: data));
    } catch (error) {
      emit(
        AsyncState<T>(
          status: AsyncStatus.error,
          data: keepData ? state.data : null,
          error: error.toString(),
          fromCache: state.fromCache,
        ),
      );
    }
  }
}
