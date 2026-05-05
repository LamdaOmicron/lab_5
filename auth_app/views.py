import secrets
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from django.conf import settings
import requests

from users.models import User
from auth_app.services import AuthService
from auth_app.dto import (
    RegisterSerializer, LoginSerializer, ForgotPasswordSerializer, 
    ResetPasswordSerializer, UserResponseSerializer
)
from auth_app.jwt_utils import verify_access_token
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes


def get_client_ip(request):
    """Получение IP адреса клиента."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class AuthMiddlewareMixin:
    """Миксин для проверки аутентификации через JWT в cookies."""
    
    def get_user_from_request(self, request):
        """
        Извлечение и проверка Access токена из cookies.
        
        Returns:
            Объект User если токен валиден, None иначе.
        """
        access_token = request.COOKIES.get('access_token')
        
        if not access_token:
            return None
        
        payload = verify_access_token(access_token)
        
        if not payload:
            return None
        
        user_id = payload.get('user_id')
        return AuthService.get_user_by_id(user_id)


@extend_schema(
    tags=['Auth'],
    summary='Регистрация пользователя',
    description='Регистрация нового пользователя с email и паролем',
    responses={
        201: OpenApiResponse(
            response=UserResponseSerializer,
            description='Пользователь успешно зарегистрирован',
            examples=[
                {
                    "message": "Пользователь успешно зарегистрирован",
                    "user": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "email": "user@example.com",
                        "phone": None,
                        "first_name": "John",
                        "last_name": "Doe",
                        "avatar_url": "",
                        "created_at": "2024-01-01T12:00:00Z"
                    }
                }
            ]
        ),
        400: OpenApiResponse(
            description='Ошибка валидации данных',
            examples=[{"error": "Пользователь с таким email уже существует"}]
        )
    }
)
@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    """Регистрация нового пользователя."""
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = AuthService.register_user(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
                first_name=serializer.validated_data.get('first_name', ''),
                last_name=serializer.validated_data.get('last_name', ''),
            )
            
            return Response({
                'message': 'Пользователь успешно зарегистрирован',
                'user': UserResponseSerializer(user).data
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Auth'],
    summary='Вход пользователя',
    description='Аутентификация пользователя с установкой JWT токенов в HttpOnly cookies',
    responses={
        200: OpenApiResponse(
            description='Успешный вход',
            examples=[
                {
                    "message": "Успешный вход",
                    "user": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "email": "user@example.com",
                        "phone": None,
                        "first_name": "John",
                        "last_name": "Doe",
                        "avatar_url": "",
                        "created_at": "2024-01-01T12:00:00Z"
                    }
                }
            ]
        ),
        401: OpenApiResponse(
            description='Неверный email или пароль',
            examples=[{"error": "Неверный email или пароль"}]
        )
    }
)
@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    """Вход пользователя с установкой cookies."""
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = AuthService.authenticate_user(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )
        
        if not user:
            raise AuthenticationFailed('Неверный email или пароль')
        
        # Генерируем токены
        access_token, refresh_token = AuthService.generate_tokens(user)
        
        # Сохраняем refresh token в БД
        AuthService.save_refresh_token(
            user=user,
            token=refresh_token,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Формируем ответ с cookies
        response = Response({
            'message': 'Успешный вход',
            'user': UserResponseSerializer(user).data
        })
        
        # Устанавливаем HttpOnly cookies
        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=False,  # True в production с HTTPS
            samesite='Lax',
            max_age=900,  # 15 минут
            path='/'
        )
        
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            secure=False,  # True в production с HTTPS
            samesite='Lax',
            max_age=604800,  # 7 дней
            path='/'
        )
        
        return response


@extend_schema(
    tags=['Auth'],
    summary='Обновление токенов',
    description='Обновление пары JWT токенов с использованием refresh токена из cookies',
    responses={
        200: OpenApiResponse(
            description='Токены успешно обновлены',
            examples=[{"message": "Токены обновлены"}]
        ),
        401: OpenApiResponse(
            description='Невалидный или отозванный refresh токен',
            examples=[{"error": "Невалидный или отозванный refresh токен"}]
        )
    }
)
@method_decorator(csrf_exempt, name='dispatch')
class RefreshTokenView(APIView):
    """Обновление пары токенов."""
    
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        
        if not refresh_token:
            raise AuthenticationFailed('Refresh токен не найден')
        
        # Проверяем токен в БД
        token_obj = AuthService.verify_refresh_token_in_db(refresh_token)
        
        if not token_obj:
            raise AuthenticationFailed('Невалидный или отозванный refresh токен')
        
        # Получаем пользователя
        user = token_obj.user
        
        # Генерируем новую пару токенов
        new_access_token, new_refresh_token = AuthService.generate_tokens(user)
        
        # Отзываем старый токен
        AuthService.revoke_token(token_obj)
        
        # Сохраняем новый refresh token
        AuthService.save_refresh_token(
            user=user,
            token=new_refresh_token,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Формируем ответ с новыми cookies
        response = Response({
            'message': 'Токены обновлены'
        })
        
        response.set_cookie(
            key='access_token',
            value=new_access_token,
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=900,
            path='/'
        )
        
        response.set_cookie(
            key='refresh_token',
            value=new_refresh_token,
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=604800,
            path='/'
        )
        
        return response


@extend_schema(
    tags=['Auth'],
    summary='Проверка авторизации',
    description='Получение данных текущего аутентифицированного пользователя',
    responses={
        200: OpenApiResponse(
            description='Данные пользователя',
            examples=[
                {
                    "user": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "email": "user@example.com",
                        "phone": None,
                        "first_name": "John",
                        "last_name": "Doe",
                        "avatar_url": "",
                        "created_at": "2024-01-01T12:00:00Z"
                    },
                    "authenticated": True
                }
            ]
        ),
        401: OpenApiResponse(
            description='Пользователь не аутентифицирован',
            examples=[{"error": "Пользователь не аутентифицирован"}]
        )
    }
)
@method_decorator(csrf_exempt, name='dispatch')
class WhoamiView(APIView):
    """Проверка статуса авторизации и получение данных пользователя."""
    
    def get(self, request):
        user = self.get_user_from_request(request)
        
        if not user:
            raise AuthenticationFailed('Пользователь не аутентифицирован')
        
        return Response({
            'user': UserResponseSerializer(user).data,
            'authenticated': True
        })


@extend_schema(
    tags=['Auth'],
    summary='Выход из системы',
    description='Завершение текущей сессии с отзывом refresh токена',
    responses={
        200: OpenApiResponse(
            description='Успешный выход',
            examples=[{"message": "Успешный выход"}]
        ),
        401: OpenApiResponse(
            description='Пользователь не аутентифицирован',
            examples=[{"error": "Пользователь не аутентифицирован"}]
        )
    }
)
@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(AuthMiddlewareMixin, APIView):
    """Завершение текущей сессии."""
    
    def post(self, request):
        user = self.get_user_from_request(request)
        
        if not user:
            raise AuthenticationFailed('Пользователь не аутентифицирован')
        
        # Находим и отзываем текущий refresh token
        refresh_token = request.COOKIES.get('refresh_token')
        
        if refresh_token:
            token_obj = AuthService.verify_refresh_token_in_db(refresh_token)
            if token_obj:
                AuthService.revoke_token(token_obj)
        
        # Очищаем cookies
        response = Response({'message': 'Успешный выход'})
        
        response.delete_cookie('access_token', path='/')
        response.delete_cookie('refresh_token', path='/')
        
        return response


@extend_schema(
    tags=['Auth'],
    summary='Выход из всех сессий',
    description='Завершение всех сессий пользователя с отзывом всех refresh токенов',
    responses={
        200: OpenApiResponse(
            description='Все сессии завершены',
            examples=[{"message": "Все сессии завершены"}]
        ),
        401: OpenApiResponse(
            description='Пользователь не аутентифицирован',
            examples=[{"error": "Пользователь не аутентифицирован"}]
        )
    }
)
@method_decorator(csrf_exempt, name='dispatch')
class LogoutAllView(AuthMiddlewareMixin, APIView):
    """Завершение всех сессий пользователя."""
    
    def post(self, request):
        user = self.get_user_from_request(request)
        
        if not user:
            raise AuthenticationFailed('Пользователь не аутентифицирован')
        
        # Отзываем все токены пользователя
        AuthService.revoke_all_user_tokens(user)
        
        # Очищаем cookies
        response = Response({'message': 'Все сессии завершены'})
        
        response.delete_cookie('access_token', path='/')
        response.delete_cookie('refresh_token', path='/')
        
        return response


@extend_schema(
    tags=['Auth'],
    summary='Инициация OAuth входа',
    description='Получение URL для перенаправления на OAuth провайдера (Yandex или VK)',
    parameters=[
        OpenApiParameter(
            name='provider',
            type=str,
            location=OpenApiParameter.PATH,
            description='OAuth провайдер (yandex или vk)',
            enum=['yandex', 'vk']
        )
    ],
    responses={
        200: OpenApiResponse(
            description='URL для авторизации',
            examples=[{"redirect_url": "https://oauth.yandex.ru/authorize?..."}]
        ),
        400: OpenApiResponse(
            description='Неподдерживаемый провайдер',
            examples=[{"error": "Неподдерживаемый провайдер"}]
        )
    }
)
@method_decorator(csrf_exempt, name='dispatch')
class OAuthInitView(View):
    """Инициация входа через OAuth провайдера."""
    
    def get(self, request, provider):
        if provider not in ['yandex', 'vk']:
            return JsonResponse({'error': 'Неподдерживаемый провайдер'}, status=400)
        
        # Генерируем state для защиты от CSRF
        state = secrets.token_urlsafe(32)
        
        # Сохраняем state в сессии для последующей проверки
        request.session[f'oauth_state_{provider}'] = state
        
        if provider == 'yandex':
            auth_url = 'https://oauth.yandex.ru/authorize'
            params = {
                'response_type': 'code',
                'client_id': settings.OAUTH_CLIENT_ID,
                'redirect_uri': settings.OAUTH_CALLBACK_URL,
                'state': state,
            }
        elif provider == 'vk':
            auth_url = 'https://id.vk.com/authorize'
            params = {
                'client_id': settings.OAUTH_CLIENT_ID,
                'redirect_uri': settings.OAUTH_CALLBACK_URL,
                'response_type': 'code',
                'state': state,
            }
        
        from urllib.parse import urlencode
        return JsonResponse({'redirect_url': f"{auth_url}?{urlencode(params)}"})


@extend_schema(
    tags=['Auth'],
    summary='OAuth callback',
    description='Обработка ответа от OAuth провайдера и создание локальной сессии',
    parameters=[
        OpenApiParameter(
            name='provider',
            type=str,
            location=OpenApiParameter.PATH,
            description='OAuth провайдер (yandex или vk)',
            enum=['yandex', 'vk']
        )
    ],
    responses={
        302: OpenApiResponse(description='Редирект после успешной авторизации'),
        400: OpenApiResponse(description='Ошибка авторизации')
    }
)
@method_decorator(csrf_exempt, name='dispatch')
class OAuthCallbackView(View):
    """Обработка ответа от OAuth провайдера."""
    
    def get(self, request, provider):
        if provider not in ['yandex', 'vk']:
            return JsonResponse({'error': 'Неподдерживаемый провайдер'}, status=400)
        
        code = request.GET.get('code')
        state = request.GET.get('state')
        
        if not code:
            return JsonResponse({'error': 'Код авторизации не получен'}, status=400)
        
        # Проверяем state для защиты от CSRF
        saved_state = request.session.get(f'oauth_state_{provider}')
        if not saved_state or state != saved_state:
            return JsonResponse({'error': 'Невалидный state параметр'}, status=400)
        
        # Удаляем state из сессии после использования
        del request.session[f'oauth_state_{provider}']
        
        # Обмениваем код на токен
        if provider == 'yandex':
            token_response = requests.post('https://oauth.yandex.ru/token', data={
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': settings.OAUTH_CLIENT_ID,
                'client_secret': settings.OAUTH_CLIENT_SECRET,
                'redirect_uri': settings.OAUTH_CALLBACK_URL,
            })
            
            if token_response.status_code != 200:
                return JsonResponse({'error': 'Ошибка получения токена от провайдера'}, status=400)
            
            token_data = token_response.json()
            access_token = token_data.get('access_token')
            
            # Получаем данные пользователя
            user_response = requests.get('https://login.yandex.ru/info', headers={
                'Authorization': f'OAuth {access_token}'
            })
            
            if user_response.status_code != 200:
                return JsonResponse({'error': 'Ошибка получения данных пользователя'}, status=400)
            
            user_data = user_response.json()
            
            oauth_user_id = str(user_data.get('id'))
            email = user_data.get('default_email')
            first_name = user_data.get('first_name', '')
            last_name = user_data.get('last_name', '')
            avatar_url = user_data.get('default_avatar_id', '')
            if avatar_url:
                avatar_url = f"https://avatars.yandex.net/get-yapic/{avatar_url}/islands-200"
        
        elif provider == 'vk':
            token_response = requests.post('https://id.vk.com/oauth2/auth', data={
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': settings.OAUTH_CLIENT_ID,
                'client_secret': settings.OAUTH_CLIENT_SECRET,
                'redirect_uri': settings.OAUTH_CALLBACK_URL,
            })
            
            if token_response.status_code != 200:
                return JsonResponse({'error': 'Ошибка получения токена от провайдера'}, status=400)
            
            token_data = token_response.json()
            access_token = token_data.get('access_token')
            
            # Получаем данные пользователя
            user_response = requests.get('https://id.vk.com/api/userinfo', headers={
                'Authorization': f'Bearer {access_token}'
            })
            
            if user_response.status_code != 200:
                return JsonResponse({'error': 'Ошибка получения данных пользователя'}, status=400)
            
            user_data = user_response.json()
            
            oauth_user_id = str(user_data.get('sub'))
            email = user_data.get('email')
            first_name = user_data.get('first_name', '')
            last_name = user_data.get('last_name', '')
            avatar_url = user_data.get('picture', '')
        
        # Находим или создаем пользователя
        user = AuthService.find_or_create_oauth_user(
            provider=provider,
            provider_id=oauth_user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            avatar_url=avatar_url
        )
        
        # Генерируем локальные токены
        access_token, refresh_token = AuthService.generate_tokens(user)
        
        # Сохраняем refresh token в БД
        AuthService.save_refresh_token(
            user=user,
            token=refresh_token,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Создаем ответ с редиректом и устанавливаем cookies
        from django.http import HttpResponseRedirect
        response = HttpResponseRedirect('/auth/login-success')
        
        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=900,
            path='/'
        )
        
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=604800,
            path='/'
        )
        
        return response


@extend_schema(
    tags=['Auth'],
    summary='Запрос сброса пароля',
    description='Отправка инструкции по сбросу пароля на email',
    responses={
        200: OpenApiResponse(
            description='Инструкция отправлена',
            examples=[{"message": "Если пользователь с таким email существует, инструкция по сбросу пароля будет отправлена"}]
        )
    }
)
@method_decorator(csrf_exempt, name='dispatch')
class ForgotPasswordView(APIView):
    """Запрос на сброс пароля."""
    
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        # Всегда возвращаем успех для предотвращения enumeration атак
        # В реальном приложении здесь была бы отправка email со ссылкой на сброс
        # Для демонстрации просто возвращаем успех
        
        # TODO: Реализовать отправку email с токеном сброса пароля
        # token = generate_password_reset_token(email)
        # send_reset_email(email, token)
        
        return Response({'message': 'Если пользователь с таким email существует, инструкция по сбросу пароля будет отправлена'})


@extend_schema(
    tags=['Auth'],
    summary='Сброс пароля',
    description='Установка нового пароля с использованием токена сброса',
    responses={
        200: OpenApiResponse(
            description='Пароль успешно изменен',
            examples=[{"message": "Пароль успешно изменен"}]
        )
    }
)
@method_decorator(csrf_exempt, name='dispatch')
class ResetPasswordView(APIView):
    """Установка нового пароля."""
    
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['password']
        
        # TODO: Реализовать проверку токена сброса пароля и установку нового пароля
        # payload = verify_password_reset_token(token)
        # if not payload:
        #     raise AuthenticationFailed('Невалидный токен сброса пароля')
        # user = User.objects.get(email=payload['email'])
        # password_hash, salt = hash_password(new_password)
        # user.password_hash = password_hash
        # user.salt = salt
        # user.save()
        
        return Response({'message': 'Пароль успешно изменен'})
