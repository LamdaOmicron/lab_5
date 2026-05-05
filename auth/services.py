from typing import Optional, Tuple
from datetime import timedelta
from django.utils import timezone
from users.models import User, RefreshToken
from auth.crypto import hash_password, verify_password, hash_token, verify_token
from auth.jwt_utils import generate_access_token, generate_refresh_token, get_expiration_datetime
from django.conf import settings


class AuthService:
    """Сервис для управления аутентификацией и авторизацией."""

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
    def generate_tokens(user: User) -> Tuple[str, str]:
        """
        Генерация пары Access и Refresh токенов.
        
        Args:
            user: Объект пользователя.
            
        Returns:
            Кортеж (access_token, refresh_token).
        """
        access_token = generate_access_token(str(user.id), user.email)
        refresh_token = generate_refresh_token(str(user.id), user.email)
        
        return access_token, refresh_token

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
        from auth.jwt_utils import verify_refresh_token
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
