from typing import Optional, Tuple
from datetime import timedelta
from django.utils import timezone
from users.models import User, RefreshToken
from auth_app.crypto import hash_password, verify_password, hash_token, verify_token
from auth_app.jwt_utils import generate_access_token, generate_refresh_token, get_expiration_datetime, get_access_token_ttl_seconds
from django.conf import settings
from common.cache.cache_service import cache_service
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Сервис для управления аутентификацией и авторизацией."""
    
    # Префиксы ключей кеша для токенов и сессий
    CACHE_PREFIX_ACCESS_TOKEN = 'auth:user:{user_id}:access:{jti}'
    CACHE_PREFIX_USER_PROFILE = 'users:profile:{user_id}'

    @staticmethod
    def _get_access_token_cache_key(user_id: str, jti: str) -> str:
        """Генерация ключа кеша для Access токена."""
        return AuthService.CACHE_PREFIX_ACCESS_TOKEN.format(user_id=user_id, jti=jti)
    
    @staticmethod
    def _get_user_profile_cache_key(user_id: str) -> str:
        """Генерация ключа кеша для профиля пользователя."""
        return AuthService.CACHE_PREFIX_USER_PROFILE.format(user_id=user_id)

    @staticmethod
    def register_user(email: str, password: str, first_name: str = '', last_name: str = '') -> User:
        """
        Регистрация нового пользователя.
        
        Args:
            email: Email пользователя.
            password: Пароль в открытом виде.
            first_name: Имя (опционально).
            last_name: Фамилия (опционально).
            
        Returns:
            Созданный объект User.
            
        Raises:
            ValueError: Если пользователь с таким email уже существует.
        """
        if User.objects.filter(email=email).exists():
            raise ValueError("Пользователь с таким email уже существует")
        
        # Хешируем пароль с уникальной солью
        password_hash, salt = hash_password(password)
        
        user = User.objects.create(
            email=email,
            password_hash=password_hash,
            salt=salt,
            first_name=first_name,
            last_name=last_name,
        )
        
        return user

    @staticmethod
    def authenticate_user(email: str, password: str) -> Optional[User]:
        """
        Аутентификация пользователя по email и паролю.
        
        Args:
            email: Email пользователя.
            password: Пароль в открытом виде.
            
        Returns:
            Объект User если аутентификация успешна, None иначе.
        """
        try:
            user = User.objects.get(email=email, deleted_at__isnull=True)
        except User.DoesNotExist:
            return None
        
        if not user.password_hash or not user.salt:
            return None
        
        if verify_password(password, user.password_hash, user.salt):
            return user
        
        return None

    @staticmethod
    def find_or_create_oauth_user(provider: str, provider_id: str, email: str, 
                                   first_name: str = '', last_name: str = '',
                                   avatar_url: str = '') -> User:
        """
        Поиск или создание пользователя через OAuth.
        
        Args:
            provider: Название провайдера ('yandex', 'vk').
            provider_id: ID пользователя у провайдера.
            email: Email пользователя.
            first_name: Имя.
            last_name: Фамилия.
            avatar_url: URL аватара.
            
        Returns:
            Объект User.
        """
        # Определяем поле для поиска по провайдеру
        provider_field = f'{provider}_id'
        
        # Пытаемся найти пользователя по OAuth ID
        filter_kwargs = {provider_field: provider_id}
        user = User.objects.filter(**filter_kwargs, deleted_at__isnull=True).first()
        
        if user:
            return user
        
        # Пытаемся найти по email
        if email:
            user = User.objects.filter(email=email, deleted_at__isnull=True).first()
            if user:
                # Привязываем OAuth ID к существующему пользователю
                setattr(user, provider_field, provider_id)
                if first_name and not user.first_name:
                    user.first_name = first_name
                if last_name and not user.last_name:
                    user.last_name = last_name
                if avatar_url and not user.avatar_url:
                    user.avatar_url = avatar_url
                user.save()
                return user
        
        # Создаем нового пользователя
        user = User.objects.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            avatar_url=avatar_url,
        )
        
        # Привязываем OAuth ID
        setattr(user, provider_field, provider_id)
        user.save()
        
        return user

    @staticmethod
    def generate_tokens(user: User) -> Tuple[str, str, str]:
        """
        Генерация пары Access и Refresh токенов.
        
        Args:
            user: Объект пользователя.
            
        Returns:
            Кортеж (access_token, jti, refresh_token).
        """
        access_token, jti = generate_access_token(str(user.id), user.email)
        refresh_token = generate_refresh_token(str(user.id), user.email)
        
        return access_token, jti, refresh_token

    @staticmethod
    def save_access_token_to_cache(user_id: str, jti: str) -> bool:
        """
        Сохранение JTI Access токена в Redis для возможности отзыва.
        
        Args:
            user_id: ID пользователя.
            jti: Уникальный идентификатор токена.
            
        Returns:
            True если успешно, False иначе.
        """
        cache_key = AuthService._get_access_token_cache_key(user_id, jti)
        ttl = get_access_token_ttl_seconds()
        
        # Храним значение "valid" чтобы подтвердить что токен активен
        result = cache_service.set(cache_key, {'status': 'valid', 'user_id': user_id}, ttl=ttl)
        
        if result:
            logger.debug(f"Saved access token JTI to cache: {cache_key} (TTL: {ttl}s)")
        
        return result

    @staticmethod
    def verify_access_token_in_cache(user_id: str, jti: str) -> bool:
        """
        Проверка наличия JTI Access токена в Redis.
        
        Args:
            user_id: ID пользователя.
            jti: Уникальный идентификатор токена.
            
        Returns:
            True если токен действителен, False если отозван или не найден.
        """
        cache_key = AuthService._get_access_token_cache_key(user_id, jti)
        cached_data = cache_service.get(cache_key)
        
        if cached_data is None:
            # Токен не найден в кеше - значит он истек или был отозван
            logger.debug(f"Access token JTI not found in cache: {cache_key}")
            return False
        
        # Проверяем что токен принадлежит этому пользователю
        if cached_data.get('user_id') != str(user_id):
            logger.warning(f"User ID mismatch for token JTI: {cache_key}")
            return False
        
        return True

    @staticmethod
    def revoke_access_token_from_cache(user_id: str, jti: str) -> bool:
        """
        Отзыв Access токена путем удаления JTI из Redis.
        
        Args:
            user_id: ID пользователя.
            jti: Уникальный идентификатор токена.
            
        Returns:
            True если успешно, False иначе.
        """
        cache_key = AuthService._get_access_token_cache_key(user_id, jti)
        result = cache_service.delete(cache_key)
        
        if result:
            logger.debug(f"Revoked access token JTI from cache: {cache_key}")
        
        return result

    @staticmethod
    def cache_user_profile(user: User, ttl: Optional[int] = None) -> bool:
        """
        Кэширование профиля пользователя.
        
        Args:
            user: Объект пользователя.
            ttl: Время жизни кеша в секундах.
            
        Returns:
            True если успешно, False иначе.
        """
        cache_key = AuthService._get_user_profile_cache_key(str(user.id))
        
        profile_data = {
            'id': str(user.id),
            'email': user.email,
            'phone': user.phone if hasattr(user, 'phone') else None,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'avatar_url': user.avatar_url if hasattr(user, 'avatar_url') else '',
            'created_at': user.created_at.isoformat() if user.created_at else None,
        }
        
        result = cache_service.set(cache_key, profile_data, ttl=ttl)
        
        if result:
            logger.debug(f"Cached user profile: {cache_key}")
        
        return result

    @staticmethod
    def get_cached_user_profile(user_id: str) -> Optional[dict]:
        """
        Получение кэшированного профиля пользователя.
        
        Args:
            user_id: ID пользователя.
            
        Returns:
            Данные профиля или None если не найдено.
        """
        cache_key = AuthService._get_user_profile_cache_key(user_id)
        return cache_service.get(cache_key)

    @staticmethod
    def invalidate_user_profile_cache(user_id: str) -> bool:
        """
        Инвалидация кэша профиля пользователя.
        
        Args:
            user_id: ID пользователя.
            
        Returns:
            True если успешно, False иначе.
        """
        cache_key = AuthService._get_user_profile_cache_key(user_id)
        return cache_service.delete(cache_key)

    @staticmethod
    def save_refresh_token(user: User, token: str, ip_address: str = None, 
                           user_agent: str = '') -> RefreshToken:
        """
        Сохранение хеша Refresh токена в БД.
        
        Args:
            user: Объект пользователя.
            token: Refresh токен в открытом виде.
            ip_address: IP адрес клиента.
            user_agent: User Agent клиента.
            
        Returns:
            Созданный объект RefreshToken.
        """
        token_hash = hash_token(token)
        expires_at = get_expiration_datetime(settings.JWT_REFRESH_EXPIRATION)
        
        refresh_token_obj = RefreshToken.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return refresh_token_obj

    @staticmethod
    def verify_refresh_token_in_db(token: str) -> Optional[RefreshToken]:
        """
        Проверка Refresh токена в базе данных.
        
        Args:
            token: Refresh токен в открытом виде.
            
        Returns:
            Объект RefreshToken если токен валиден, None иначе.
        """
        # Находим все не отозванные токены пользователя
        # Мы не можем искать по хешу напрямую, поэтому перебираем
        # В продакшене можно оптимизировать, храня часть токена для поиска
        
        # Получаем payload токена чтобы найти пользователя
        from auth_app.jwt_utils import verify_refresh_token
        payload = verify_refresh_token(token)
        
        if not payload:
            return None
        
        user_id = payload.get('user_id')
        
        try:
            user = User.objects.get(id=user_id, deleted_at__isnull=True)
        except User.DoesNotExist:
            return None
        
        # Проверяем все активные refresh токены пользователя
        for rt in RefreshToken.objects.filter(user=user, revoked=False, expires_at__gt=timezone.now()):
            if verify_token(token, rt.token_hash):
                return rt
        
        return None

    @staticmethod
    def revoke_token(refresh_token: RefreshToken):
        """
        Отзыв токена.
        
        Args:
            refresh_token: Объект RefreshToken для отзыва.
        """
        refresh_token.revoke()

    @staticmethod
    def revoke_all_user_tokens(user: User):
        """
        Отзыв всех Refresh токенов пользователя.
        
        Args:
            user: Объект пользователя.
        """
        RefreshToken.objects.filter(user=user, revoked=False).update(revoked=True)

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[User]:
        """
        Получение пользователя по ID.
        
        Args:
            user_id: UUID пользователя.
            
        Returns:
            Объект User если найден, None иначе.
        """
        try:
            return User.objects.get(id=user_id, deleted_at__isnull=True)
        except User.DoesNotExist:
            return None
