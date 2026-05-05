from django.urls import path
from auth.views import (
    RegisterView, LoginView, RefreshTokenView, WhoamiView,
    LogoutView, LogoutAllView, OAuthInitView, OAuthCallbackView,
    ForgotPasswordView, ResetPasswordView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('refresh/', RefreshTokenView.as_view(), name='auth-refresh'),
    path('whoami/', WhoamiView.as_view(), name='auth-whoami'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('logout-all/', LogoutAllView.as_view(), name='auth-logout-all'),
    path('oauth/<str:provider>/', OAuthInitView.as_view(), name='auth-oauth-init'),
    path('oauth/<str:provider>/callback/', OAuthCallbackView.as_view(), name='auth-oauth-callback'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='auth-forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='auth-reset-password'),
]
