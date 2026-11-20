import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/models.dart';
import '../../../core/network/api_exception.dart';
import '../data/auth_repository.dart';

enum AuthStatus { unknown, authenticated, unauthenticated }

class AuthState extends Equatable {
  const AuthState({
    this.status = AuthStatus.unknown,
    this.user,
    this.submitting = false,
    this.error,
  });

  final AuthStatus status;
  final SessionUser? user;
  final bool submitting;
  final String? error;

  AuthState copyWith({
    AuthStatus? status,
    SessionUser? user,
    bool? submitting,
    String? error,
    bool clearError = false,
    bool clearUser = false,
  }) {
    return AuthState(
      status: status ?? this.status,
      user: clearUser ? null : (user ?? this.user),
      submitting: submitting ?? this.submitting,
      error: clearError ? null : (error ?? this.error),
    );
  }

  @override
  List<Object?> get props => [status, user?.id, submitting, error];
}

class AuthCubit extends Cubit<AuthState> {
  AuthCubit(this._repository) : super(const AuthState());

  final AuthRepository _repository;

  Future<void> bootstrap() async {
    final user = await _repository.restoreSession();
    if (user == null) {
      emit(const AuthState(status: AuthStatus.unauthenticated));
    } else {
      emit(AuthState(status: AuthStatus.authenticated, user: user));
    }
  }

  Future<bool> login(String email, String password) async {
    emit(state.copyWith(submitting: true, clearError: true));
    try {
      final user = await _repository.login(email, password);
      emit(
        AuthState(
          status: AuthStatus.authenticated,
          user: user,
        ),
      );
      return true;
    } on ApiException catch (error) {
      emit(
        state.copyWith(
          submitting: false,
          error: error.message,
          status: AuthStatus.unauthenticated,
        ),
      );
      return false;
    } catch (_) {
      emit(
        state.copyWith(
          submitting: false,
          error: 'Could not sign in. Please try again.',
          status: AuthStatus.unauthenticated,
        ),
      );
      return false;
    }
  }

  Future<bool> register({
    required String fullName,
    required String email,
    required String password,
    required String accountType,
    required String locale,
    String? organizationName,
  }) async {
    emit(state.copyWith(submitting: true, clearError: true));
    try {
      final user = await _repository.register(
        fullName: fullName,
        email: email,
        password: password,
        accountType: accountType,
        locale: locale,
        organizationName: organizationName,
      );
      emit(AuthState(status: AuthStatus.authenticated, user: user));
      return true;
    } on ApiException catch (error) {
      emit(
        state.copyWith(
          submitting: false,
          error: error.message,
          status: AuthStatus.unauthenticated,
        ),
      );
      return false;
    } catch (_) {
      emit(
        state.copyWith(
          submitting: false,
          error: 'Could not create the account. Please try again.',
          status: AuthStatus.unauthenticated,
        ),
      );
      return false;
    }
  }

  Future<void> refreshUser() async {
    if (state.status != AuthStatus.authenticated) return;
    try {
      final user = await _repository.me();
      emit(state.copyWith(user: user));
    } catch (_) {
      // Non-fatal; the next authenticated request will surface real auth errors.
    }
  }

  Future<void> logout() async {
    await _repository.logout();
    emit(const AuthState(status: AuthStatus.unauthenticated));
  }

  void sessionExpired() {
    if (state.status == AuthStatus.authenticated) {
      emit(
        const AuthState(
          status: AuthStatus.unauthenticated,
          error: 'Your session expired. Please sign in again.',
        ),
      );
    }
  }

  void clearError() => emit(state.copyWith(clearError: true));
}
